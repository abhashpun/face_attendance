import React, { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import { toast } from 'react-toastify';
import { 
  Container, 
  Button, 
  Card, 
  Table, 
  Modal, 
  Form, 
  Alert, 
  Spinner,
  Badge
} from 'react-bootstrap';

function StudentManagement() {
  const [students, setStudents] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
      const [formData, setFormData] = useState({
      student_id: '',
      name: '',
      email: '',
      semester: 1
    });
  
  const webcamRef = useRef(null);

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await axios.get('/students');
      setStudents(response.data);
    } catch (error) {
      toast.error('Failed to fetch students');
    }
  };

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
  }, [webcamRef]);

  const retake = () => {
    setCapturedImage(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!capturedImage) {
      toast.error('Please capture a photo first');
      return;
    }

    setLoading(true);
    try {
      // First, encode the face
      const encodingResponse = await axios.post('/encode-face', {
        image: capturedImage
      });

      const studentData = {
        ...formData,
        semester: Number(formData.semester),
        face_encoding: encodingResponse.data.encoding
      };

      await axios.post('/students', studentData);
      
      toast.success('Student added successfully');
      setShowModal(false);
      setFormData({ student_id: '', name: '', email: '', semester: 1 });
      setCapturedImage(null);
      fetchStudents();
      window.dispatchEvent(new Event('stats:update'));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add student');
    }
    setLoading(false);
  };

  const handleDelete = async (studentId) => {
    if (window.confirm('Are you sure you want to delete this student?')) {
      try {
        await axios.delete(`/students/${studentId}`);
        toast.success('Student deleted successfully');
        fetchStudents();
        window.dispatchEvent(new Event('stats:update'));
      } catch (error) {
        toast.error('Failed to delete student');
      }
    }
  };

  const videoConstraints = {
    width: 400,
    height: 300,
    facingMode: "user"
  };

  return (
    <Container className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Student Management</h2>
        <Button onClick={() => setShowModal(true)} variant="primary">
          Add Student
        </Button>
      </div>

      <Card>
        <Card.Body>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Semester</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.id}>
                  <td>{student.student_id}</td>
                  <td>{student.name}</td>
                  <td>{student.email}</td>
                  <td>{student.semester ?? '-'}</td>
                  <td>{new Date(student.created_at).toLocaleDateString()}</td>
                  <td>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(student.student_id)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Add Student Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Add New Student</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleSubmit}>
          <Modal.Body>
            <div className="row">
              <div className="col-md-6">
                <Form.Group className="mb-3">
                  <Form.Label>Student ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={formData.student_id}
                    onChange={(e) => setFormData({...formData, student_id: e.target.value})}
                    required
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Name</Form.Label>
                  <Form.Control
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Email</Form.Label>
                  <Form.Control
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Semester</Form.Label>
                  <Form.Select
                    value={formData.semester}
                    onChange={(e) => setFormData({ ...formData, semester: Number(e.target.value) })}
                    required
                  >
                    {[1,2,3,4,5,6,7,8].map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </div>
              
              <div className="col-md-6">
                <h6>Face Photo</h6>
                {!capturedImage ? (
                  <div className="text-center">
                    <Webcam
                      ref={webcamRef}
                      screenshotFormat="image/jpeg"
                      videoConstraints={videoConstraints}
                      className="img-fluid"
                    />
                    <div className="mt-2">
                      <Button onClick={capture} variant="primary" size="sm">
                        Capture Photo
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center">
                    <img 
                      src={capturedImage} 
                      alt="Captured" 
                      className="img-fluid"
                      style={{ maxWidth: '100%', height: 'auto' }}
                    />
                    <div className="mt-2">
                      <Button onClick={retake} variant="secondary" size="sm">
                        Retake
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="primary"
              disabled={loading || !capturedImage}
            >
              {loading ? (
                <>
                  <Spinner
                    as="span"
                    animation="border"
                    size="sm"
                    role="status"
                    aria-hidden="true"
                    className="me-2"
                  />
                  Adding...
                </>
              ) : (
                'Add Student'
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
}

export default StudentManagement; 