package com.university.web.controller;

import com.university.ejb.service.StudentServiceBean;
import com.university.persistence.entity.Student;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.inject.Inject;
import javax.inject.Named;
import java.io.Serializable;
import java.util.List;

/**
 * JSF Managed Bean for Student Management Module.
 */
@Named("studentBean")
@RequestScoped
public class StudentBean implements Serializable {

    @EJB
    private StudentServiceBean studentService;

    @Inject
    private AuthBean authBean;

    // Form fields for add/edit
    private Long studentId;
    private String firstName;
    private String lastName;
    private String email;
    private String department;
    private Integer yearOfStudy;
    private String password;
    private String searchQuery;

    private List<Student> students;
    private Student selectedStudent;

    /**
     * Load all students.
     */
    public List<Student> getAllStudents() {
        if (students == null) {
            students = studentService.getAllStudents();
        }
        return students;
    }

    /**
     * Search students by name.
     */
    public String searchStudents() {
        if (searchQuery != null && !searchQuery.trim().isEmpty()) {
            students = studentService.searchStudents(searchQuery.trim());
        } else {
            students = studentService.getAllStudents();
        }
        return null;
    }

    /**
     * Prepare the edit form by loading student data.
     */
    public String editStudent(Long id) {
        try {
            selectedStudent = studentService.getStudentById(id);
            this.studentId = selectedStudent.getStudentId();
            this.firstName = selectedStudent.getFirstName();
            this.lastName = selectedStudent.getLastName();
            this.email = selectedStudent.getEmail();
            this.department = selectedStudent.getDepartment();
            this.yearOfStudy = selectedStudent.getYearOfStudy();
        } catch (Exception e) {
            addError("Could not load student: " + e.getMessage());
        }
        return null;
    }

    /**
     * Save a new student.
     */
    public String saveStudent() {
        try {
            studentService.registerStudent(firstName, lastName, email, department, yearOfStudy, password);
            addInfo("Student registered successfully.");
            clearForm();
            students = null; // refresh
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    /**
     * Update an existing student.
     */
    public String updateStudent() {
        try {
            studentService.updateStudent(studentId, firstName, lastName, department, yearOfStudy);
            addInfo("Student updated successfully.");
            clearForm();
            students = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    /**
     * Delete a student by ID.
     */
    public String deleteStudent(Long id) {
        try {
            studentService.deleteStudent(id);
            addInfo("Student deleted successfully.");
            students = null;
        } catch (Exception e) {
            addError("Could not delete student: " + e.getMessage());
        }
        return null;
    }

    /**
     * Get student count for dashboard.
     */
    public Long getStudentCount() {
        return studentService.getStudentCount();
    }

    private void clearForm() {
        studentId = null;
        firstName = null;
        lastName = null;
        email = null;
        department = null;
        yearOfStudy = null;
        password = null;
    }

    private void addInfo(String msg) {
        FacesContext.getCurrentInstance().addMessage(null,
                new FacesMessage(FacesMessage.SEVERITY_INFO, "Success", msg));
    }

    private void addError(String msg) {
        FacesContext.getCurrentInstance().addMessage(null,
                new FacesMessage(FacesMessage.SEVERITY_ERROR, "Error", msg));
    }

    // Getters and Setters
    public Long getStudentId() {
        return studentId;
    }

    public void setStudentId(Long studentId) {
        this.studentId = studentId;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public Integer getYearOfStudy() {
        return yearOfStudy;
    }

    public void setYearOfStudy(Integer yearOfStudy) {
        this.yearOfStudy = yearOfStudy;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getSearchQuery() {
        return searchQuery;
    }

    public void setSearchQuery(String searchQuery) {
        this.searchQuery = searchQuery;
    }

    public List<Student> getStudents() {
        return getAllStudents();
    }

    public Student getSelectedStudent() {
        return selectedStudent;
    }
}
