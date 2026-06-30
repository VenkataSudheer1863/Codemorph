package com.university.persistence.entity;

import javax.persistence.*;
import java.io.Serializable;

/**
 * JPA Entity representing a student's Result for a Course.
 */
@Entity
@Table(name = "results", uniqueConstraints = @UniqueConstraint(columnNames = { "student_id", "course_id" }))
@NamedQueries({
        @NamedQuery(name = "Result.findAll", query = "SELECT r FROM Result r"),
        @NamedQuery(name = "Result.findByStudent", query = "SELECT r FROM Result r WHERE r.student.studentId = :studentId"),
        @NamedQuery(name = "Result.findByCourse", query = "SELECT r FROM Result r WHERE r.course.courseId = :courseId"),
        @NamedQuery(name = "Result.findByStudentAndCourse", query = "SELECT r FROM Result r WHERE r.student.studentId = :studentId AND r.course.courseId = :courseId")
})
public class Result implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "result_id")
    private Long resultId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "student_id", nullable = false)
    private Student student;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "course_id", nullable = false)
    private Course course;

    @Column(name = "grade", nullable = false, length = 5)
    private String grade; // e.g., A+, A, B+, B, C, D, F

    @Column(name = "marks_obtained")
    private Double marksObtained;

    @Column(name = "total_marks")
    private Double totalMarks;

    @Column(name = "remarks", length = 500)
    private String remarks;

    // Constructors
    public Result() {
    }

    public Result(Student student, Course course, String grade, Double marksObtained, Double totalMarks) {
        this.student = student;
        this.course = course;
        this.grade = grade;
        this.marksObtained = marksObtained;
        this.totalMarks = totalMarks;
    }

    // Getters and Setters
    public Long getResultId() {
        return resultId;
    }

    public void setResultId(Long resultId) {
        this.resultId = resultId;
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

    public String getGrade() {
        return grade;
    }

    public void setGrade(String grade) {
        this.grade = grade;
    }

    public Double getMarksObtained() {
        return marksObtained;
    }

    public void setMarksObtained(Double marksObtained) {
        this.marksObtained = marksObtained;
    }

    public Double getTotalMarks() {
        return totalMarks;
    }

    public void setTotalMarks(Double totalMarks) {
        this.totalMarks = totalMarks;
    }

    public String getRemarks() {
        return remarks;
    }

    public void setRemarks(String remarks) {
        this.remarks = remarks;
    }

    public Double getPercentage() {
        if (totalMarks != null && totalMarks > 0 && marksObtained != null) {
            return (marksObtained / totalMarks) * 100;
        }
        return 0.0;
    }

    @Override
    public String toString() {
        return "Result{resultId=" + resultId + ", grade=" + grade + ", marks=" + marksObtained + "/" + totalMarks + "}";
    }
}
