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
        students: response.data.recognized_students
      });
      toast.success(response.data.message);
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
              </ul>
              
              {result && (
                <Alert variant={result.success ? 'success' : 'danger'} className="mt-3">
                  <Alert.Heading>
                    {result.success ? 'Success!' : 'Error'}
                  </Alert.Heading>
                  <p>{result.message}</p>
                  {result.students && (
                    <div>
                      <strong>Recognized students:</strong>
                      <ul className="mb-0">
                        {result.students.map((student, index) => (
                          <li key={index}>{student}</li>
                        ))}
                      </ul>
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