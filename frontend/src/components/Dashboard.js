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
    const onFocus = () => fetchStats();
    const onStatsUpdate = () => fetchStats();
    window.addEventListener('focus', onFocus);
    window.addEventListener('stats:update', onStatsUpdate);
    return () => {
      window.removeEventListener('focus', onFocus);
      window.removeEventListener('stats:update', onStatsUpdate);
    };
  }, []);

  const fetchStats = async () => {
    try {
      const { data } = await axios.get('/stats');
      const semesterStats = Array.isArray(data?.semester_stats)
        ? data.semester_stats.map((s) => ({
            semester: Number(s.semester) || 0,
            total: Number(s.total) || 0,
            presentToday: Number(s.present_today) || 0,
            absentToday: Math.max(0, (Number(s.total) || 0) - (Number(s.present_today) || 0)),
            attendanceRate: Number(s.attendance_rate) || 0,
          }))
        : Array.from({ length: 8 }, (_, i) => ({
            semester: i + 1,
            total: 0,
            presentToday: 0,
            absentToday: 0,
            attendanceRate: 0,
          }));

      const normalized = {
        totalStudents: data?.total_students ?? 0,
        presentToday: data?.today_attendance ?? 0,
        absentToday: Math.max(0, (data?.total_students ?? 0) - (data?.today_attendance ?? 0)),
        attendanceRate: Number(data?.attendance_rate ?? 0),
        semesterStats,
      };
      console.table({
        Total_Students: normalized.totalStudents,
        Present_Today: normalized.presentToday,
        Absent_Today: normalized.absentToday,
        Attendance_Rate: `${normalized.attendanceRate.toFixed(1)}%`
      });
      setStats(normalized);
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
        data: [stats?.presentToday || 0, stats?.absentToday || 0],
        backgroundColor: ['#28a745', '#dc3545'],
        borderWidth: 1,
      },
    ],
  };

  const barData = {
    labels: ['Total Students', 'Present Today', 'Absent Today'],
    datasets: [
      {
        label: 'Count',
        data: [stats?.totalStudents || 0, stats?.presentToday || 0, stats?.absentToday || 0],
        backgroundColor: ['#007bff', '#28a745', '#dc3545'],
      },
    ],
  };

  return (
    <Container className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="mb-0">Dashboard</h2>
        <Button variant="outline-secondary" size="sm" onClick={fetchStats}>Refresh</Button>
      </div>
      
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
              <h2 className="text-primary">{stats?.totalStudents || 0}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Present Today</Card.Title>
              <h2 className="text-success">{stats?.presentToday || 0}</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Absent Today</Card.Title>
              <h2 className="text-danger">
                {stats?.absentToday || 0}
              </h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Attendance Rate</Card.Title>
              <h2 className="text-info">{(stats?.attendanceRate ?? 0).toFixed(1)}%</h2>
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

      {/* Semester-wise Stats */}
      <Row className="mt-4">
        <Col md={12}>
          <Card>
            <Card.Body>
              <Card.Title>Semester-wise Attendance Today</Card.Title>
              <div className="table-responsive">
                <table className="table table-striped table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Semester</th>
                      <th>Total Students</th>
                      <th>Present Today</th>
                      <th>Absent Today</th>
                      <th>Attendance Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(stats?.semesterStats || []).map((s) => (
                      <tr key={s.semester}>
                        <td>{s.semester}</td>
                        <td>{s.total}</td>
                        <td className="text-success">{s.presentToday}</td>
                        <td className="text-danger">{s.absentToday}</td>
                        <td className="text-info">{s.attendanceRate.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default Dashboard; 