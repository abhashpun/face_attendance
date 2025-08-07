import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-toastify';
import { Container, Row, Col, Card, Button, Spinner } from 'react-bootstrap';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/stats');
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
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

  const pieData = {
    labels: ['Present Today', 'Absent Today'],
    datasets: [
      {
        data: [stats?.today_attendance || 0, (stats?.total_students || 0) - (stats?.today_attendance || 0)],
        backgroundColor: ['#28a745', '#dc3545'],
        borderWidth: 1,
      },
    ],
  };

  const barData = {
    labels: ['Total Students', 'Present Today'],
    datasets: [
      {
        label: 'Count',
        data: [stats?.total_students || 0, stats?.today_attendance || 0],
        backgroundColor: ['#007bff', '#28a745'],
      },
    ],
  };

  return (
    <Container className="mt-4">
      <h2 className="mb-4">Dashboard</h2>
      
      {/* Quick Actions */}
      <Row className="mb-4">
        <Col md={4}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Mark Attendance</Card.Title>
              <Card.Text>Use face recognition to mark student attendance</Card.Text>
              <Link to="/attendance">
                <Button variant="primary">Start Attendance</Button>
              </Link>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Manage Students</Card.Title>
              <Card.Text>Add, edit, or remove student records</Card.Text>
              <Link to="/students">
                <Button variant="success">Manage Students</Button>
              </Link>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>View History</Card.Title>
              <Card.Text>Check attendance records and reports</Card.Text>
              <Link to="/history">
                <Button variant="info">View History</Button>
              </Link>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Statistics */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Total Students</Card.Title>
              <h2 className="text-primary">{stats?.total_students || 0}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Present Today</Card.Title>
              <h2 className="text-success">{stats?.today_attendance || 0}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Absent Today</Card.Title>
              <h2 className="text-danger">
                {(stats?.total_students || 0) - (stats?.today_attendance || 0)}
              </h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Attendance Rate</Card.Title>
              <h2 className="text-info">{stats?.attendance_rate?.toFixed(1) || 0}%</h2>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row>
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>Today's Attendance Distribution</Card.Title>
              <Pie data={pieData} />
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>Student Overview</Card.Title>
              <Bar 
                data={barData} 
                options={{
                  scales: {
                    y: {
                      beginAtZero: true
                    }
                  }
                }}
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default Dashboard; 