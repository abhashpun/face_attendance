import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import { toast } from 'react-toastify';
import { Container, Button, Card, Alert, Spinner } from 'react-bootstrap';

function AttendanceMarking() {
  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
    setResult(null);
  }, [webcamRef]);

  const retake = () => {
    setCapturedImage(null);
    setResult(null);
  };

  const markAttendance = async () => {
    if (!capturedImage) return;

    setProcessing(true);
    try {
      const response = await axios.post('/attendance/mark', {
        image: capturedImage
      });

      setResult({
        success: true,
        message: response.data.message,
        recognized_students: response.data.recognized_students || [],
        already_marked_students: response.data.already_marked_students || [],
        unknown_faces_count: response.data.unknown_faces_count || 0
      });
      
      // Show appropriate toast based on the result
      if (response.data.recognized_students && response.data.recognized_students.length > 0) {
        toast.success(`Attendance marked for: ${response.data.recognized_students.join(', ')}`);
      }
      if (response.data.already_marked_students && response.data.already_marked_students.length > 0) {
        toast.warning(`Attendance already done for: ${response.data.already_marked_students.join(', ')}`);
      }
      if (response.data.unknown_faces_count > 0) {
        toast.error(`Unknown face detected (${response.data.unknown_faces_count} face(s))`);
      }
      window.dispatchEvent(new Event('stats:update'));
    } catch (error) {
      setResult({
        success: false,
        message: error.response?.data?.detail || 'Failed to mark attendance'
      });
      toast.error(error.response?.data?.detail || 'Failed to mark attendance');
    }
    setProcessing(false);
  };

  const videoConstraints = {
    width: 640,
    height: 480,
    facingMode: "user"
  };

  return (
    <Container className="mt-4">
      <h2 className="mb-4">Mark Attendance</h2>
      
      <div className="row">
        <div className="col-md-8">
          <Card>
            <Card.Body>
              <h5 className="card-title">Camera</h5>
              {!capturedImage ? (
                <div className="text-center">
                  <Webcam
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    videoConstraints={videoConstraints}
                    className="img-fluid"
                  />
                  <div className="mt-3">
                    <Button onClick={capture} variant="primary">
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
                  <div className="mt-3">
                    <Button onClick={retake} variant="secondary" className="me-2">
                      Retake
                    </Button>
                    <Button 
                      onClick={markAttendance} 
                      variant="success"
                      disabled={processing}
                    >
                      {processing ? (
                        <>
                          <Spinner
                            as="span"
                            animation="border"
                            size="sm"
                            role="status"
                            aria-hidden="true"
                            className="me-2"
                          />
                          Processing...
                        </>
                      ) : (
                        'Mark Attendance'
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
        
        <div className="col-md-4">
          <Card>
            <Card.Body>
              <h5 className="card-title">Instructions</h5>
              <ul className="list-unstyled">
                <li>• Position your face in the camera</li>
                <li>• Ensure good lighting</li>
                <li>• Look directly at the camera</li>
                <li>• Click "Capture Photo"</li>
                <li>• Click "Mark Attendance" to submit</li>
                <li>• System will detect unknown faces</li>
                <li>• Duplicate attendance will be prevented</li>
              </ul>
              
              {result && (
                <Alert variant={result.success ? 'success' : 'danger'} className="mt-3">
                  <Alert.Heading>
                    {result.success ? 'Result' : 'Error'}
                  </Alert.Heading>
                  <p>{result.message}</p>
                  
                  {result.recognized_students && result.recognized_students.length > 0 && (
                    <div className="mb-2">
                      <strong className="text-success">✓ Attendance marked for:</strong>
                      <ul className="mb-0">
                        {result.recognized_students.map((student, index) => (
                          <li key={index}>{student}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {result.already_marked_students && result.already_marked_students.length > 0 && (
                    <div className="mb-2">
                      <strong className="text-warning">⚠ Attendance already done for:</strong>
                      <ul className="mb-0">
                        {result.already_marked_students.map((student, index) => (
                          <li key={index}>{student}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {result.unknown_faces_count > 0 && (
                    <div className="mb-2">
                      <strong className="text-danger">✗ Unknown faces detected:</strong>
                      <p className="mb-0">{result.unknown_faces_count} face(s) not recognized</p>
                    </div>
                  )}
                </Alert>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>
    </Container>
  );
}

export default AttendanceMarking; 