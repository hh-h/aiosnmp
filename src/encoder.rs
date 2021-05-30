use lazy_static::lazy_static;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyBytes, PyInt, PyString};
use regex::Regex;

use crate::Error;

lazy_static! {
    static ref OID_REGEX: Regex = Regex::new(r"^\d+(?:\.\d+)+$").unwrap();
}

#[pyclass]
#[text_signature = "()"]
pub struct Encoder {
    m_stack: Vec<Vec<u8>>,
}

#[pymethods]
impl Encoder {
    #[new]
    fn new() -> Self {
        let m_stack: Vec<Vec<u8>> = vec![Vec::new()];
        Encoder { m_stack }
    }

    #[text_signature = "($self, number, class)"]
    #[args(class = "None")]
    fn enter(&mut self, number: u8, class: Option<u8>) {
        let class = class.unwrap_or(0x00);
        self._emit_tag(number, 0x20, class);
        self.m_stack.push(Vec::new())
    }

    fn exit(&mut self) -> PyResult<()> {
        if self.m_stack.len() == 1 {
            return Err(Error::new_err("Tag stack is empty."));
        }

        let value = self.m_stack.pop().unwrap();
        self._emit_length(value.len());
        self._emit(value);

        Ok(())
    }

    #[args(number = "None", typ = "None", class = "None")]
    fn write(&mut self, value: &PyAny, number: Option<u8>, typ: Option<u8>, class: Option<u8>) -> PyResult<()> {
        let number = match number {
            Some(number) => number,
            None => {
                if value.is_instance::<PyBool>().unwrap() {
                    0x01
                } else if value.is_instance::<PyInt>().unwrap() {
                    0x02
                } else if value.is_instance::<PyString>().unwrap() || value.is_instance::<PyBytes>().unwrap() {
                    0x04
                } else if value.is_none() {
                    0x05
                } else if value.get_type().name()? == "IPv4Address" {
                    0x40
                } else {
                    return Err(Error::new_err("Cannot determine Number for value type"));
                }
            }
        };
        let typ = typ.unwrap_or(0x00);
        let class = class.unwrap_or(0x00);
        let value = self._encode_value(number, value)?;

        self._emit_tag(number, typ, class);
        self._emit_length(value.len());
        self._emit(value);

        Ok(())
    }

    fn output<'a>(&self, py: Python<'a>) -> PyResult<&'a PyBytes> {
        if self.m_stack.len() != 1 {
            return Err(Error::new_err("Stack is not empty."));
        }

        Ok(PyBytes::new(py, &self.m_stack[0]))
    }
}

impl Encoder {
    fn _encode_value(&self, number: u8, value: &PyAny) -> PyResult<Vec<u8>> {
        let value = match number {
            0x02 | 0x0A => Encoder::_encode_integer(value)?,
            0x04 | 0x13 => Encoder::_encode_octet_string(value)?,
            0x01 => Encoder::_encode_boolean(value)?,
            0x05 => Encoder::_encode_null(value),
            0x06 => Encoder::_encode_object_identifier(value)?,
            0x40 => Encoder::encode_ip_address(value)?,
            _ => return Err(Error::new_err(format!("Unhandled Number {} value {}", number, value))),
        };
        Ok(value)
    }

    fn _encode_boolean(value: &PyAny) -> PyResult<Vec<u8>> {
        let value = if value.is_true()? { 255 } else { 0 };
        Ok(vec![value])
    }

    fn _encode_integer(value: &PyAny) -> PyResult<Vec<u8>> {
        let value = value.extract::<i128>()?;
        let (mut value, negative, limit) = if value < 0 {
            (-value as u128, true, 0x80)
        } else {
            (value as u128, false, 0x7F)
        };

        let mut values = Vec::new();
        while value > limit {
            values.push((value & 0xFF) as u8);
            value >>= 8;
        }
        values.push((value & 0xFF) as u8);

        if negative {
            for v in values.iter_mut() {
                *v = 0xFF - *v;
            }
            for v in values.iter_mut() {
                if *v == 0xFF {
                    *v = 0x00;
                    continue;
                }
                *v += 1;
                break;
            }
        }

        let len = values.len();
        if negative && values[len - 1] == 0x7F {
            values.push(0xFF);
        }

        values.reverse();
        Ok(values)
    }

    fn _encode_octet_string(value: &PyAny) -> PyResult<Vec<u8>> {
        if value.is_instance::<PyString>()? {
            Ok(value.extract::<String>()?.into_bytes())
        } else {
            Ok(value.downcast::<PyBytes>()?.as_bytes().to_vec())
        }
    }

    fn _encode_null(_value: &PyAny) -> Vec<u8> {
        Vec::new()
    }

    fn _encode_object_identifier(value: &PyAny) -> PyResult<Vec<u8>> {
        let value = value.extract::<&str>().unwrap();
        if !OID_REGEX.is_match(value) {
            return Err(Error::new_err("Illegal object identifier"));
        }
        let value: Vec<u32> = value
            .split('.')
            .map(|x| x.parse::<u32>())
            .filter(|x| x.is_ok())
            .map(|x| x.unwrap())
            .collect();

        if value[0] > 39 || value[1] > 39 {
            return Err(Error::new_err("Illegal object identifier"));
        }

        let mut values = vec![40 * value[0] + value[1]];
        values.extend(&value[2..]);
        values.reverse();
        let mut result: Vec<u8> = Vec::new();
        for value in values.iter() {
            result.push((value & 0x7F) as u8);
            let mut cmp = *value;
            while cmp > 0x7F {
                cmp >>= 7;
                result.push((0x80 | (cmp & 0x7F)) as u8);
            }
        }
        result.reverse();
        Ok(result)
    }
    fn encode_ip_address(value: &PyAny) -> PyResult<Vec<u8>> {
        let value = value.call_method0("__int__")?.extract::<u32>()?;
        Ok(value.to_be_bytes().to_vec())
    }

    fn _emit_tag(&mut self, number: u8, typ: u8, class: u8) {
        self._emit_tag_short(number, typ, class)
    }

    fn _emit_tag_short(&mut self, number: u8, typ: u8, class: u8) {
        self._emit_simple(number | typ | class)
    }

    fn _emit(&mut self, value: Vec<u8>) {
        let len = self.m_stack.len();
        self.m_stack[len - 1].extend(value)
    }

    fn _emit_simple(&mut self, value: u8) {
        let len = self.m_stack.len();
        self.m_stack[len - 1].push(value)
    }

    fn _emit_length(&mut self, length: usize) {
        if length < 128 {
            self._emit_length_short(length)
        } else {
            self._emit_length_long(length)
        }
    }

    fn _emit_length_short(&mut self, length: usize) {
        self._emit_simple(length as u8)
    }

    fn _emit_length_long(&mut self, length: usize) {
        let mut values: Vec<u8> = Vec::new();
        let mut length = length;
        while length > 0 {
            values.push((length & 0xFF) as u8);
            length >>= 8;
        }
        values.reverse();
        let head = (0x80 | values.len()) as u8;
        self._emit_simple(head);
        self._emit(values);
    }
}
