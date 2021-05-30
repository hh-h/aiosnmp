use pyo3::prelude::*;

#[pyclass]
#[derive(Copy, Clone)]
pub struct Tag {
    #[pyo3(get)]
    pub number: u8,
    #[pyo3(get)]
    pub typ: u8,
    #[pyo3(get)]
    pub cls: u8,
}

#[pymethods]
impl Tag {
    #[new]
    fn new(number: u8, typ: u8, cls: u8) -> Self {
        Tag { number, typ, cls }
    }
}
