package com.university.persistence.entity;

import javax.persistence.*;
import java.io.Serializable;
import java.time.LocalDate;

/**
 * JPA Entity representing an Exam schedule for a Course.
 */
@Entity
@Table(name = "exams")
@NamedQueries({
        @NamedQuery(name = "Exam.findAll", query = "SELECT e FROM Exam e ORDER BY e.examDate"),
        @NamedQuery(name = "Exam.findByCourse", query = "SELECT e FROM Exam e WHERE e.course.courseId = :courseId ORDER BY e.examDate"),
        @NamedQuery(name = "Exam.findUpcoming", query = "SELECT e FROM Exam e WHERE e.examDate >= :today ORDER BY e.examDate")
})
public class Exam implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "exam_id")
    private Long examId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "course_id", nullable = false)
    private Course course;

    @Column(name = "exam_date", nullable = false)
    private LocalDate examDate;

    @Column(name = "exam_type", length = 50)
    private String examType; // e.g., "Midterm", "Final", "Quiz"

    @Column(name = "location", length = 200)
    private String location;

    @Column(name = "duration_minutes")
    private Integer durationMinutes;

    // Constructors
    public Exam() {
    }

    public Exam(Course course, LocalDate examDate, String examType, String location, Integer durationMinutes) {
        this.course = course;
        this.examDate = examDate;
        this.examType = examType;
        this.location = location;
        this.durationMinutes = durationMinutes;
    }

    // Getters and Setters
    public Long getExamId() {
        return examId;
    }

    public void setExamId(Long examId) {
        this.examId = examId;
    }

    public Course getCourse() {
        return course;
    }

    public void setCourse(Course course) {
        this.course = course;
    }

    public LocalDate getExamDate() {
        return examDate;
    }

    public void setExamDate(LocalDate examDate) {
        this.examDate = examDate;
    }

    public String getExamType() {
        return examType;
    }

    public void setExamType(String examType) {
        this.examType = examType;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public Integer getDurationMinutes() {
        return durationMinutes;
    }

    public void setDurationMinutes(Integer durationMinutes) {
        this.durationMinutes = durationMinutes;
    }

    public String getCourseName() {
        return (course != null) ? course.getCourseName() : "Unknown";
    }

    @Override
    public String toString() {
        return "Exam{examId=" + examId + ", examDate=" + examDate + ", examType=" + examType + "}";
    }
}
