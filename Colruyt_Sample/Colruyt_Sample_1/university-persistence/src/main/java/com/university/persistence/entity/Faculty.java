package com.university.persistence.entity;

import javax.persistence.*;
import java.io.Serializable;
import java.util.List;

/**
 * JPA Entity representing a Faculty member in the University system.
 */
@Entity
@Table(name = "faculty")
@NamedQueries({
    @NamedQuery(name = "Faculty.findAll",
                query = "SELECT f FROM Faculty f ORDER BY f.name"),
    @NamedQuery(name = "Faculty.findByEmail",
                query = "SELECT f FROM Faculty f WHERE f.email = :email"),
    @NamedQuery(name = "Faculty.findByDepartment",
                query = "SELECT f FROM Faculty f WHERE f.department = :department ORDER BY f.name"),
    @NamedQuery(name = "Faculty.searchByName",
                query = "SELECT f FROM Faculty f WHERE LOWER(f.name) LIKE :name ORDER BY f.name")
})
public class Faculty implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "faculty_id")
    private Long facultyId;

    @Column(name = "name", nullable = false, length = 200)
    private String name;

    @Column(name = "email", nullable = false, unique = true, length = 200)
    private String email;

    @Column(name = "department", nullable = false, length = 100)
    private String department;

    @Column(name = "designation", nullable = false, length = 100)
    private String designation;

    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    @OneToMany(mappedBy = "faculty", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Course> courses;

    // Constructors
    public Faculty() {}

    public Faculty(String name, String email, String department, String designation, String passwordHash) {
        this.name = name;
        this.email = email;
        this.department = department;
        this.designation = designation;
        this.passwordHash = passwordHash;
    }

    // Getters and Setters
    public Long getFacultyId() { return facultyId; }
    public void setFacultyId(Long facultyId) { this.facultyId = facultyId; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getDepartment() { return department; }
    public void setDepartment(String department) { this.department = department; }

    public String getDesignation() { return designation; }
    public void setDesignation(String designation) { this.designation = designation; }

    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }

    public List<Course> getCourses() { return courses; }
    public void setCourses(List<Course> courses) { this.courses = courses; }

    @Override
    public String toString() {
        return "Faculty{facultyId=" + facultyId + ", name=" + name + ", department=" + department + "}";
    }
}
