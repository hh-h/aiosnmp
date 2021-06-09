use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyTuple};

use crate::tag::Tag;
use crate::Error;

struct Data(usize, Vec<u8>);

#[pyclass]
#[text_signature = "(bytes)"]
pub struct Decoder {
    m_stack: Vec<Data>,
    m_tag: Option<Tag>,
}

#[pymethods]
impl Decoder {
    #[new]
    fn new(data: Vec<u8>) -> Self {
        let m_stack: Vec<Data> = vec![Data(0, data)];
        Decoder { m_stack, m_tag: None }
    }

    #[text_signature = "($self)"]
    fn peek(&mut self) -> PyResult<Tag> {
        if self.end_of_input() {
            return Err(Error::new_err("Input is empty."));
        }
        if self.m_tag.is_none() {
            self.m_tag = Some(self.read_tag()?);
        }
        Ok(self.m_tag.unwrap())
    }

    #[text_signature = "($self, number)"]
    #[args(number = "None")]
    fn read(&mut self, py: Python, number: Option<u8>) -> PyResult<(Tag, PyObject)> {
        if self.end_of_input() {
            return Err(Error::new_err("Input is empty."));
        }

        let tag = self.peek()?;
        let length = self.read_length()?;
        let number = match number {
            Some(number) => number,
            None => tag.number | tag.cls,
        };

        let value = self.read_value(py, number, length)?;
        self.m_tag = None;

        Ok((tag, value))
    }

    #[text_signature = "($self)"]
    fn eof(&mut self) -> bool {
        self.end_of_input()
    }

    #[text_signature = "($self)"]
    fn enter(&mut self) -> PyResult<()> {
        let tag = self.peek().unwrap();
        if tag.typ != 0x20 {
            return Err(Error::new_err("Cannot enter a non-constructed tag."));
        }
        let length = self.read_length()?;
        let data = self.read_bytes(length)?;
        self.m_stack.push(Data(0, data));
        self.m_tag = None;

        Ok(())
    }

    #[text_signature = "($self)"]
    fn exit(&mut self) -> PyResult<()> {
        if self.m_stack.len() == 1 {
            return Err(Error::new_err("Tag stack is empty."));
        }
        self.m_stack.pop();
        self.m_tag = None;

        Ok(())
    }
}

impl Decoder {
    fn read_tag(&mut self) -> PyResult<Tag> {
        let byte = self.read_byte()?;
        let cls = byte & 0xC0;
        let typ = byte & 0x20;
        let mut number = byte & 0x1F;

        if number == 0x1F {
            number = 0;
            loop {
                let byte = self.read_byte()?;
                number = (number << 7) | (byte & 0x7F);
                if byte & 0x80 == 0 {
                    break;
                }
            }
        }

        Ok(Tag { number, typ, cls })
    }

    fn read_length(&mut self) -> PyResult<u32> {
        let byte = self.read_byte()?;
        let mut length: u32 = 0;
        if byte & 0x80 > 0 {
            let count = byte & 0x7F;
            if count == 0x7F {
                return Err(Error::new_err("ASN1 syntax error"));
            }
            let data = self.read_bytes(count as u32)?;
            for byte in data.into_iter() {
                length = (length << 8) | byte as u32;
            }
        } else {
            length = byte as u32;
        }

        Ok(length)
    }

    fn read_value(&mut self, py: Python, number: u8, length: u32) -> PyResult<PyObject> {
        let data = self.read_bytes(length)?;
        match number {
            0x01 => Ok(Decoder::decode_boolean(data)?.to_object(py)),
            0x02 | 0x0A | 0x41 | 0x42 | 0x43 | 0x46 | 0x47 => Ok(Decoder::decode_integer(data).to_object(py)),
            0x04 => Ok(PyBytes::new(py, &Decoder::decode_octet_string(data)).to_object(py)),
            0x05 => Ok(Decoder::decode_null(data)?.to_object(py)),
            0x06 => Ok(Decoder::decode_object_identifier(data)?.to_object(py)),
            0x13 | 0x16 | 0x17 => Ok(Decoder::decode_printable_string(data).to_object(py)),
            0x80 | 0x81 | 0x82 => Ok(().to_object(py)),
            0x40 => Ok(Decoder::decode_ip_address(py, data)?.to_object(py)),
            _ => Ok(PyBytes::new(py, &data).to_object(py)),
        }
    }

    fn read_byte(&mut self) -> PyResult<u8> {
        let mut data = self.m_stack.last_mut().unwrap();
        let byte = match data.1.get(data.0) {
            Some(byte) => *byte,
            None => return Err(Error::new_err("Premature end of input.")),
        };
        data.0 += 1;

        Ok(byte)
    }

    fn read_bytes(&mut self, count: u32) -> PyResult<Vec<u8>> {
        let count = count as usize;
        let mut data = self.m_stack.last_mut().unwrap();
        let bytes = match data.1.get(data.0..data.0 + count) {
            Some(bytes) => bytes.to_vec(),
            None => return Err(Error::new_err("Premature end of input.")),
        };

        data.0 += count;

        Ok(bytes)
    }

    fn end_of_input(&mut self) -> bool {
        let data = self.m_stack.last().unwrap();
        data.0 == data.1.len()
    }

    fn decode_boolean(data: Vec<u8>) -> PyResult<bool> {
        if data.len() != 1 {
            return Err(Error::new_err("ASN1 syntax error"));
        }

        Ok(data[0] > 0)
    }

    fn decode_integer(data: Vec<u8>) -> i128 {
        let mut bytes = data;
        let negative = bytes[0] & 0x80 > 0;
        if negative {
            let last_index = bytes.len() - 1;
            for (i, byte) in bytes.iter_mut().enumerate() {
                *byte = 0xFF - *byte;
                if i == last_index {
                    *byte += 1;
                }
            }
        }

        let mut value: i128 = 0;
        for byte in bytes {
            value = (value << 8) | byte as i128;
        }
        if negative {
            value = -value;
        }
        value
    }

    fn decode_octet_string(data: Vec<u8>) -> Vec<u8> {
        data
    }

    fn decode_null(data: Vec<u8>) -> PyResult<()> {
        if !data.is_empty() {
            return Err(Error::new_err("ASN1 syntax error"));
        }

        Ok(())
    }

    fn decode_object_identifier(data: Vec<u8>) -> PyResult<String> {
        let mut result: Vec<u32> = Vec::new();
        let mut value: u32 = 0;
        for byte in data.into_iter() {
            if value == 0 && byte == 0x80 {
                return Err(Error::new_err("ASN1 syntax error"));
            }

            value = (value << 7) | (byte & 0x7F) as u32;
            if byte & 0x80 == 0 {
                result.push(value);
                value = 0;
            }
        }

        if result.is_empty() || result[0] > 1599 {
            return Err(Error::new_err("ASN1 syntax error"));
        }

        let mut vec = vec![result[0] / 40, result[0] % 40];
        vec.extend_from_slice(&result[1..]);
        let result: Vec<String> = vec.iter().map(|&x| x.to_string()).collect();
        Ok(format!(".{}", result.join(".")))
    }

    fn decode_printable_string(data: Vec<u8>) -> String {
        String::from_utf8(data).unwrap()
    }

    fn decode_ip_address(py: Python, data: Vec<u8>) -> PyResult<&PyAny> {
        let mut int_ip: u32 = data[0] as u32 * 256_u32.pow(3);
        int_ip += data[1] as u32 * 256_u32.pow(2);
        int_ip += data[2] as u32 * 256_u32;
        int_ip += data[3] as u32;
        let pt = PyTuple::new(py, &[int_ip]);
        let ipaddress = PyModule::import(py, "ipaddress")?;
        let ipv4 = ipaddress.call1("IPv4Address", pt)?;
        Ok(ipv4)
    }
}
