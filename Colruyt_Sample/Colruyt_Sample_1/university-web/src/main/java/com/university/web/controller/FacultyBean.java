package com.university.web.controller;

import com.university.ejb.service.FacultyServiceBean;
import com.university.ejb.service.CourseServiceBean;
import com.university.persistence.entity.Faculty;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.inject.Named;
import java.io.Serializable;
import java.util.List;

/**
 * JSF Managed Bean for Faculty Management Module.
 */
@Named("facultyBean")
@RequestScoped
public class FacultyBean implements Serializable {

    @EJB
    private FacultyServiceBean facultyService;

    @EJB
    private CourseServiceBean courseService;

    // Form fields
    private Long facultyId;
    private String name;
    private String email;
    private String department;
    private String designation;
    private String password;
    private String searchQuery;

    private List<Faculty> facultyList;

    public List<Faculty> getAllFaculty() {
        if (facultyList == null) {
            facultyList = facultyService.getAllFaculty();
        }
        return facultyList;
    }

    public String searchFaculty() {
        if (searchQuery != null && !searchQuery.trim().isEmpty()) {
            facultyList = facultyService.searchFaculty(searchQuery.trim());
        } else {
            facultyList = facultyService.getAllFaculty();
        }
        return null;
    }

    public String editFaculty(Long id) {
        try {
            Faculty f = facultyService.getFacultyById(id);
            this.facultyId = f.getFacultyId();
            this.name = f.getName();
            this.email = f.getEmail();
            this.department = f.getDepartment();
            this.designation = f.getDesignation();
        } catch (Exception e) {
            addError("Could not load faculty: " + e.getMessage());
        }
        return null;
    }

    public String saveFaculty() {
        try {
            facultyService.addFaculty(name, email, department, designation, password);
            addInfo("Faculty member added successfully.");
            clearForm();
            facultyList = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    public String updateFaculty() {
        try {
            facultyService.updateFaculty(facultyId, name, department, designation);
            addInfo("Faculty updated successfully.");
            clearForm();
            facultyList = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    public String deleteFaculty(Long id) {
        try {
            facultyService.deleteFaculty(id);
            addInfo("Faculty member deleted.");
            facultyList = null;
        } catch (Exception e) {
            addError("Could not delete faculty: " + e.getMessage());
        }
        return null;
    }

    public Long getFacultyCount() {
        return facultyService.getFacultyCount();
    }

    private void clearForm() {
        facultyId = null;
        name = null;
        email = null;
        department = null;
        designation = null;
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
    public Long getFacultyId() {
        return facultyId;
    }

    public void setFacultyId(Long facultyId) {
        this.facultyId = facultyId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
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

    public String getDesignation() {
        return designation;
    }

    public void setDesignation(String designation) {
        this.designation = designation;
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

    public List<Faculty> getFacultyList() {
        return getAllFaculty();
    }
}
