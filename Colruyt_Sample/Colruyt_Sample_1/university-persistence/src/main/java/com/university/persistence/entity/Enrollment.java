package com.university.persistence.entity;

import javax.persistence.*;
import java.io.Serializable;

/**
 * JPA Entity representing a student's Enrollment in a Course.
 */
@Entity
@Table(name = "enrollments", uniqueConstraints = @UniqueConstraint(columnNames = { "student_id", "course_id",
        "semester" }))
@NamedQueries({
        @NamedQuery(name = "Enrollment.findAll", query = "SELECT e FROM Enrollment e"),
        @NamedQuery(name = "Enrollment.findByStudent", query = "SELECT e FROM Enrollment e WHERE e.student.studentId = :studentId"),
        @NamedQuery(name = "Enrollment.findByCourse", query = "SELECT e FROM Enrollment e WHERE e.course.courseId = :courseId"),
        @NamedQuery(name = "Enrollment.findByStudentAndCourse", query = "SELECT e FROM Enrollment e WHERE e.student.studentId = :studentId AND e.course.courseId = :courseId"),
        @NamedQuery(name = "Enrollment.findByStudentAndSemester", query = "SELECT e FROM Enrollment e WHERE e.student.studentId = :studentId AND e.semester = :semester")
})
public class Enrollment implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "enrollment_id")
    private Long enrollmentId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "student_id", nullable = false)
    private Student student;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "course_id", nullable = false)
    private Course course;

    @Column(name = "semester", nullable = false, length = 20)
    private String semester;

    // Constructors
    public Enrollment() {
    }

    public Enrollment(Student student, Course course, String semester) {
        this.student = student;
        this.course = course;
        this.semester = semester;
    }

    // Getters and Setters
    public Long getEnrollmentId() {
        return enrollmentId;
    }

    public void setEnrollmentId(Long enrollmentId) {
        this.enrollmentId = enrollmentId;
    }

    public Student getStudent() {
        return student;
    }

    public void setStudent(Student student) {
        this.student = student;
    }

    public Course getCourse() {
        return course;
    }

    public void setCourse(Course course) {
        this.course = course;
    }

    public String getSemester() {
        return semester;
    }

    public void setSemester(String semester) {
        this.semester = semester;
    }

    @Override
    public String toString() {
        return "Enrollment{enrollmentId=" + enrollmentId + ", semester=" + semester + "}";
    }
}
