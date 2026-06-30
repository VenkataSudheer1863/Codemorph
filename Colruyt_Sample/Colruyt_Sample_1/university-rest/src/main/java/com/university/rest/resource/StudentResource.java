package com.university.rest.resource;

import com.university.ejb.service.StudentServiceBean;
import com.university.persistence.entity.Student;

import javax.ejb.EJB;
import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.util.List;

/**
 * JAX-RS REST Resource for Student operations.
 * Exposes RESTful API endpoints for external system integration.
 */
@Path("/students")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class StudentResource {

    @EJB
    private StudentServiceBean studentService;

    /**
     * GET /api/students - Retrieve all students
     */
    @GET
    public Response getAllStudents() {
        try {
            List<Student> students = studentService.getAllStudents();
            return Response.ok(students).build();
        } catch (Exception e) {
            return Response.serverError().entity("{\"error\": \"" + e.getMessage() + "\"}").build();
        }
    }

    /**
     * GET /api/students/{id} - Retrieve a student by ID
     */
    @GET
    @Path("/{id}")
    public Response getStudentById(@PathParam("id") Long id) {
        try {
            Student student = studentService.getStudentById(id);
            return Response.ok(student).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * GET /api/students/search?name={name} - Search students by name
     */
    @GET
    @Path("/search")
    public Response searchStudents(@QueryParam("name") String name) {
        if (name == null || name.trim().isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"Search name parameter is required\"}")
                    .build();
        }
        List<Student> students = studentService.searchStudents(name);
        return Response.ok(students).build();
    }

    /**
     * GET /api/students/department/{dept} - Get students by department
     */
    @GET
    @Path("/department/{dept}")
    public Response getByDepartment(@PathParam("dept") String department) {
        List<Student> students = studentService.getStudentsByDepartment(department);
        return Response.ok(students).build();
    }

    /**
     * POST /api/students - Register a new student
     */
    @POST
    public Response createStudent(StudentRequest request) {
        try {
            Student student = studentService.registerStudent(
                    request.getFirstName(), request.getLastName(), request.getEmail(),
                    request.getDepartment(), request.getYearOfStudy(), request.getPassword());
            return Response.status(Response.Status.CREATED).entity(student).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * PUT /api/students/{id} - Update student details
     */
    @PUT
    @Path("/{id}")
    public Response updateStudent(@PathParam("id") Long id, StudentRequest request) {
        try {
            Student student = studentService.updateStudent(
                    id, request.getFirstName(), request.getLastName(),
                    request.getDepartment(), request.getYearOfStudy());
            return Response.ok(student).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * DELETE /api/students/{id} - Delete a student
     */
    @DELETE
    @Path("/{id}")
    public Response deleteStudent(@PathParam("id") Long id) {
        try {
            studentService.deleteStudent(id);
            return Response.noContent().build();
        } catch (Exception e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * Simple DTO for student request payload.
     */
    public static class StudentRequest {
        private String firstName;
        private String lastName;
        private String email;
        private String department;
        private Integer yearOfStudy;
        private String password;

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
    }
}
