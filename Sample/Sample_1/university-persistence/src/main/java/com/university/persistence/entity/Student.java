package com.university.persistence.entity;

import javax.persistence.*;
import java.io.Serializable;
import java.util.List;

/**
 * JPA Entity representing a Student in the University system.
 */
@Entity
@Table(name = "students")
@NamedQueries({
    @NamedQuery(name = "Student.findAll",
                query = "SELECT s FROM Student s ORDER BY s.lastName, s.firstName"),
    @NamedQuery(name = "Student.findByEmail",
                query = "SELECT s FROM Student s WHERE s.email = :email"),
    @NamedQuery(name = "Student.findByDepartment",
                query = "SELECT s FROM Student s WHERE s.department = :department ORDER BY s.lastName"),
    @NamedQuery(name = "Student.searchByName",
                query = "SELECT s FROM Student s WHERE LOWER(s.firstName) LIKE :name OR LOWER(s.lastName) LIKE :name ORDER BY s.lastName")
})
public class Student implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "student_id")
    private Long studentId;

    @Column(name = "first_name", nullable = false, length = 100)
    private String firstName;

    @Column(name = "last_name", nullable = false, length = 100)
    private String lastName;

    @Column(name = "email", nullable = false, unique = true, length = 200)
    private String email;

    @Column(name = "department", nullable = false, length = 100)
    private String department;

    @Column(name = "year_of_study", nullable = false)
    private Integer yearOfStudy;

    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    @OneToMany(mappedBy = "student", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Enrollment> enrollments;

    @OneToMany(mappedBy = "student", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Result> results;

    // Constructors
    public Student() {}

    public Student(String firstName, String lastName, String email, String department,
                   Integer yearOfStudy, String passwordHash) {
        this.firstName = firstName;
        this.lastName = lastName;
        this.email = email;
        this.department = department;
        this.yearOfStudy = yearOfStudy;
        this.passwordHash = passwordHash;
    }

    // Getters and Setters
    public Long getStudentId() { return studentId; }
    public void setStudentId(Long studentId) { this.studentId = studentId; }

    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }

    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getDepartment() { return department; }
    public void setDepartment(String department) { this.department = department; }

    public Integer getYearOfStudy() { return yearOfStudy; }
    public void setYearOfStudy(Integer yearOfStudy) { this.yearOfStudy = yearOfStudy; }

    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }

    public List<Enrollment> getEnrollments() { return enrollments; }
    public void setEnrollments(List<Enrollment> enrollments) { this.enrollments = enrollments; }

    public List<Result> getResults() { return results; }
    public void setResults(List<Result> results) { this.results = results; }

    public String getFullName() { return firstName + " " + lastName; }

    @Override
    public String toString() {
        return "Student{studentId=" + studentId + ", name=" + getFullName() + ", email=" + email + "}";
    }
}
