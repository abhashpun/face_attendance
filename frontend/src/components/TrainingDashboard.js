import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { 
  Container, 
  Card, 
  Button, 
  Row, 
  Col, 
  ProgressBar, 
  Alert,
  Badge,
  Table,
  Spinner,
  Modal,
  Form
} from 'react-bootstrap';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

function TrainingDashboard() {
  const [loading, setLoading] = useState(false);
  const [trainingLoading, setTrainingLoading] = useState(false);
  const [dataStats, setDataStats] = useState(null);
  const [modelPerformance, setModelPerformance] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [trainingHistory, setTrainingHistory] = useState([]);
  const [showTrainingModal, setShowTrainingModal] = useState(false);
  const [modelType, setModelType] = useState('svm');
  const [trainingResult, setTrainingResult] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, performanceRes, recommendationsRes] = await Promise.all([
        axios.get('/training/data-statistics'),
        axios.get('/training/performance'),
        axios.get('/training/recommendations')
      ]);

      setDataStats(statsRes.data);
      setModelPerformance(performanceRes.data);
      setRecommendations(recommendationsRes.data.recommendations || []);
      
      if (performanceRes.data.success && performanceRes.data.evaluation) {
        setTrainingHistory(performanceRes.data.evaluation.training_history || []);
      }
    } catch (error) {
      toast.error('Failed to fetch training data');
      console.error('Error fetching training data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCollectData = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/training/collect-data');
      if (response.data.success) {
        toast.success(`Collected ${response.data.total_samples} samples from ${response.data.unique_students} students`);
        fetchData(); // Refresh data
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error('Failed to collect training data');
    } finally {
      setLoading(false);
    }
  };

  const handleTrainModel = async () => {
    setTrainingLoading(true);
    try {
      const response = await axios.post('/training/train-model', { model_type: modelType });
      if (response.data.success) {
        setTrainingResult(response.data);
        toast.success(`Model trained successfully! Accuracy: ${(response.data.accuracy * 100).toFixed(2)}%`);
        setShowTrainingModal(false);
        fetchData(); // Refresh data
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error('Failed to train model');
    } finally {
      setTrainingLoading(false);
    }
  };

  const getQualityColor = (score) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'danger';
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 0.9) return 'success';
    if (accuracy >= 0.8) return 'warning';
    return 'danger';
  };

  if (loading) {
    return (
      <Container className="mt-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>AI Training Dashboard</h2>
        <div>
          <Button 
            variant="outline-primary" 
            onClick={handleCollectData}
            disabled={loading}
            className="me-2"
          >
            Collect Data
          </Button>
          <Button 
            variant="primary" 
            onClick={() => setShowTrainingModal(true)}
            disabled={loading}
          >
            Train Model
          </Button>
        </div>
      </div>

      {/* Data Statistics */}
      {dataStats && (
        <Row className="mb-4">
          <Col md={6}>
            <Card>
              <Card.Header>
                <h5>Data Statistics</h5>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <div className="text-center">
                      <h3>{dataStats.total_students}</h3>
                      <p className="text-muted">Total Students</p>
                    </div>
                  </Col>
                  <Col md={6}>
                    <div className="text-center">
                      <h3>{dataStats.students_with_faces}</h3>
                      <p className="text-muted">With Face Data</p>
                    </div>
                  </Col>
                </Row>
                <ProgressBar 
                  now={dataStats.face_coverage_percentage} 
                  label={`${dataStats.face_coverage_percentage.toFixed(1)}%`}
                  className="mb-3"
                />
                <div className="text-center">
                  <Badge bg={getQualityColor(dataStats.average_quality_score)}>
                    Avg Quality: {dataStats.average_quality_score.toFixed(1)}
                  </Badge>
                </div>
              </Card.Body>
            </Card>
          </Col>
          <Col md={6}>
            <Card>
              <Card.Header>
                <h5>Quality Distribution</h5>
              </Card.Header>
              <Card.Body>
                <Doughnut
                  data={{
                    labels: ['High Quality', 'Medium Quality', 'Low Quality'],
                    datasets: [{
                      data: [
                        dataStats.quality_distribution.high,
                        dataStats.quality_distribution.medium,
                        dataStats.quality_distribution.low
                      ],
                      backgroundColor: ['#28a745', '#ffc107', '#dc3545']
                    }]
                  }}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: {
                        position: 'bottom'
                      }
                    }
                  }}
                />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Model Performance */}
      {modelPerformance && modelPerformance.success && (
        <Row className="mb-4">
          <Col md={6}>
            <Card>
              <Card.Header>
                <h5>Model Performance</h5>
              </Card.Header>
              <Card.Body>
                {modelPerformance.evaluation.model_metrics && (
                  <div>
                    <div className="text-center mb-3">
                      <h2>
                        {(modelPerformance.evaluation.model_metrics.accuracy * 100).toFixed(1)}%
                      </h2>
                      <Badge bg={getAccuracyColor(modelPerformance.evaluation.model_metrics.accuracy)}>
                        Accuracy
                      </Badge>
                    </div>
                    <Table size="sm">
                      <tbody>
                        <tr>
                          <td>Model Type:</td>
                          <td>{modelPerformance.evaluation.model_metrics.model_type}</td>
                        </tr>
                        <tr>
                          <td>Training Samples:</td>
                          <td>{modelPerformance.evaluation.model_metrics.training_samples}</td>
                        </tr>
                        <tr>
                          <td>Test Samples:</td>
                          <td>{modelPerformance.evaluation.model_metrics.test_samples}</td>
                        </tr>
                        <tr>
                          <td>Unique Students:</td>
                          <td>{modelPerformance.evaluation.model_metrics.unique_students}</td>
                        </tr>
                      </tbody>
                    </Table>
                  </div>
                )}
              </Card.Body>
            </Card>
          </Col>
          <Col md={6}>
            <Card>
              <Card.Header>
                <h5>Training History</h5>
              </Card.Header>
              <Card.Body>
                {trainingHistory.length > 0 ? (
                  <Line
                    data={{
                      labels: trainingHistory.map(h => new Date(h.date).toLocaleDateString()),
                      datasets: [{
                        label: 'Accuracy',
                        data: trainingHistory.map(h => h.accuracy * 100),
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                      }]
                    }}
                    options={{
                      responsive: true,
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 100
                        }
                      }
                    }}
                  />
                ) : (
                  <p className="text-muted text-center">No training history available</p>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card className="mb-4">
          <Card.Header>
            <h5>Training Recommendations</h5>
          </Card.Header>
          <Card.Body>
            {recommendations.map((rec, index) => (
              <Alert key={index} variant="info" className="mb-2">
                {rec}
              </Alert>
            ))}
          </Card.Body>
        </Card>
      )}

      {/* Training Result */}
      {trainingResult && (
        <Card className="mb-4">
          <Card.Header>
            <h5>Latest Training Result</h5>
          </Card.Header>
          <Card.Body>
            <Alert variant="success">
              <h6>{trainingResult.message}</h6>
              <p>Accuracy: {(trainingResult.accuracy * 100).toFixed(2)}%</p>
            </Alert>
          </Card.Body>
        </Card>
      )}

      {/* Training Modal */}
      <Modal show={showTrainingModal} onHide={() => setShowTrainingModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Train Face Recognition Model</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Model Type</Form.Label>
              <Form.Select 
                value={modelType} 
                onChange={(e) => setModelType(e.target.value)}
              >
                <option value="svm">Support Vector Machine (Linear)</option>
                <option value="rbf">Support Vector Machine (RBF)</option>
              </Form.Select>
            </Form.Group>
            <Alert variant="info">
              <strong>Note:</strong> Training may take several minutes depending on the amount of data.
              Make sure you have collected sufficient training data first.
            </Alert>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowTrainingModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={handleTrainModel}
            disabled={trainingLoading}
          >
            {trainingLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Training...
              </>
            ) : (
              'Start Training'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default TrainingDashboard; 