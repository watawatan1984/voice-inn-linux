use pyo3::prelude::*;

mod recorder;
use recorder::AudioRecorder;

#[pyclass(unsendable)]
struct PyAudioRecorder {
    inner: AudioRecorder,
}

#[pymethods]
impl PyAudioRecorder {
    #[new]
    fn new() -> Self {
        PyAudioRecorder {
            inner: AudioRecorder::new(),
        }
    }

    fn start(&mut self, file_path: String, input_device_index: Option<usize>) -> PyResult<u32> {
        self.inner.start(file_path, input_device_index).map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to start recording: {}", e))
        })
    }

    fn stop(&mut self) -> PyResult<()> {
        self.inner.stop();
        Ok(())
    }

    fn get_stats(&self) -> PyResult<(f32, f32, f32)> {
        Ok(self.inner.get_stats())
    }

    fn is_silence(&self, energy_threshold: f32, peak_threshold: f32, min_duration: f32) -> PyResult<bool> {
        let config = recorder::VadConfig {
            energy_threshold,
            peak_threshold,
            min_duration,
        };
        Ok(self.inner.is_silence(&config))
    }
}

#[pyfunction]
fn get_input_devices() -> PyResult<Vec<(String, u32)>> {
    recorder::get_input_devices_list().map_err(|e| {
        pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to list devices: {}", e))
    })
}

/// A Python module implemented in Rust.
#[pymodule]
fn rust_core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyAudioRecorder>()?;
    m.add_function(wrap_pyfunction!(get_input_devices, m)?)?;
    Ok(())
}
