package com.university.persistence.entity;

import javax.persistence.*;
import java.io.Serializable;
import java.util.List;

/**
 * JPA Entity representing a Course in the University system.
 */
@Entity
@Table(name = "courses")
@NamedQueries({
        @NamedQuery(name = "Course.findAll", query = "SELECT c FROM Course c ORDER BY c.courseName"),
        @NamedQuery(name = "Course.findByDepartment", query = "SELECT c FROM Course c WHERE c.department = :department ORDER BY c.courseName"),
        @NamedQuery(name = "Course.findByFaculty", query = "SELECT c FROM Course c WHERE c.faculty.facultyId = :facultyId"),
        @NamedQuery(name = "Course.searchByName", query = "SELECT c FROM Course c WHERE LOWER(c.courseName) LIKE :name ORDER BY c.courseName")
})
public class Course implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "course_id")
    private Long courseId;

    @Column(name = "course_name", nullable = false, length = 200)
    private String courseName;

    @Column(name = "credits", nullable = false)
    private Integer credits;

    @Column(name = "department", nullable = false, length = 100)
    private String department;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "faculty_id")
    private Faculty faculty;

    @OneToMany(mappedBy = "course", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Enrollment> enrollments;

    @OneToMany(mappedBy = "course", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Exam> exams;

    @OneToMany(mappedBy = "course", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Result> results;

    // Constructors
    public Course() {
    }

    public Course(String courseName, Integer credits, String department, Faculty faculty) {
        this.courseName = courseName;
        this.credits = credits;
        this.department = department;
        this.faculty = faculty;
    }

    // Getters and Setters
    public Long getCourseId() {
        return courseId;
    }

    public void setCourseId(Long courseId) {
        this.courseId = courseId;
    }

    public String getCourseName() {
        return courseName;
    }

    public void setCourseName(String courseName) {
        this.courseName = courseName;
    }

    public Integer getCredits() {
        return credits;
    }

    public void setCredits(Integer credits) {
        this.credits = credits;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public Faculty getFaculty() {
        return faculty;
    }

    public void setFaculty(Faculty faculty) {
        this.faculty = faculty;
    }

    public List<Enrollment> getEnrollments() {
        return enrollments;
    }

    public void setEnrollments(List<Enrollment> enrollments) {
        this.enrollments = enrollments;
    }

    public List<Exam> getExams() {
        return exams;
    }

    public void setExams(List<Exam> exams) {
        this.exams = exams;
    }

    public List<Result> getResults() {
        return results;
    }

    public void setResults(List<Result> results) {
        this.results = results;
    }

    public String getFacultyName() {
        return (faculty != null) ? faculty.getName() : "Not Assigned";
    }

    @Override
    public String toString() {
        return "Course{courseId=" + courseId + ", courseName=" + courseName + ", credits=" + credits + "}";
    }
}
