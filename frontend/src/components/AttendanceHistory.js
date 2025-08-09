import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { 
  Container, 
  Card, 
  Table, 
  Button, 
  Form, 
  Row, 
  Col,
  Spinner,
  Badge
} from 'react-bootstrap';
import { format } from 'date-fns';

function AttendanceHistory() {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dateFilter, setDateFilter] = useState('');

  useEffect(() => {
    fetchAttendance();
  }, [dateFilter]);

  const fetchAttendance = async () => {
    try {
      const params = dateFilter ? { date_filter: dateFilter } : {};
      const response = await axios.get('/attendance', { params });
      setAttendance(response.data);
    } catch (error) {
      toast.error('Failed to fetch attendance records');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (attendanceId) => {
    if (window.confirm('Are you sure you want to delete this attendance record?')) {
      try {
        await axios.delete(`/attendance/${attendanceId}`);
        toast.success('Attendance record deleted successfully');
        fetchAttendance();
      } catch (error) {
        toast.error('Failed to delete attendance record');
      }
    }
  };

  const exportToCSV = () => {
    const headers = ['Student ID', 'Student Name', 'Semester', 'Date', 'Time'];
    const csvContent = [
      headers.join(','),
      ...attendance.map(record => [
        record.student_id,
        record.student_name,
        record.student_semester ?? '',
        record.date,
        record.time
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_${format(new Date(), 'yyyy-MM-dd')}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
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
        <h2>Attendance History</h2>
        <Button onClick={exportToCSV} variant="success">
          Export to CSV
        </Button>
      </div>

      <Card className="mb-4">
        <Card.Body>
          <Row>
            <Col md={4}>
              <Form.Group>
                <Form.Label>Filter by Date</Form.Label>
                <Form.Control
                  type="date"
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value)}
                />
              </Form.Group>
            </Col>
            <Col md={4} className="d-flex align-items-end">
              <Button 
                variant="secondary" 
                onClick={() => setDateFilter('')}
              >
                Clear Filter
              </Button>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      <Card>
        <Card.Body>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Student Name</th>
                <th>Semester</th>
                <th>Date</th>
                <th>Time</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {attendance.length === 0 ? (
                <tr>
                  <td colSpan="5" className="text-center">
                    No attendance records found
                  </td>
                </tr>
              ) : (
                attendance.map((record) => (
                  <tr key={record.id}>
                    <td>{record.student_id}</td>
                                      <td>{record.student_name}</td>
                  <td>{record.student_semester ?? '-'}</td>
                  <td>
                    <Badge bg="info">
                      {format(new Date(record.date), 'MMM dd, yyyy')}
                    </Badge>
                  </td>
                  <td>{record.time}</td>
                    <td>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(record.id)}
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      <div className="mt-3">
        <p className="text-muted">
          Total records: {attendance.length}
        </p>
      </div>
    </Container>
  );
}

export default AttendanceHistory; 