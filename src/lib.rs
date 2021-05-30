use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::{create_exception, wrap_pymodule};

use crate::decoder::Decoder;
use crate::encoder::Encoder;
use crate::tag::Tag;

mod decoder;
mod encoder;
mod tag;

create_exception!(module, Error, PyException);

#[pymodule]
fn asn1_rust(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Encoder>()?;
    m.add_class::<Decoder>()?;
    m.add_class::<Tag>()?;
    m.add("Error", py.get_type::<Error>())?;

    Ok(())
}

#[pymodule]
fn aiosnmp(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pymodule!(asn1_rust))?;

    let sys = PyModule::import(py, "sys")?;
    let sys_modules: &PyDict = sys.getattr("modules")?.downcast()?;
    sys_modules.set_item("aiosnmp.asn1_rust", m.getattr("asn1_rust")?)?;
    Ok(())
}
