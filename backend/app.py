<!DOCTYPE html>
<html>
<head>
    <title>Time to Seconds Converter</title>
</head>
<body>
    <h2>Convert Time to Seconds</h2>

    <form action="convert" method="post">
        Hours:
        <input type="text" name="hours"><br><br>

        Minutes:
        <input type="text" name="minutes"><br><br>

        <input type="submit" value="Convert">
    </form>
</body>
</html>


import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class TimeServlet extends HttpServlet {

    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
                          throws ServletException, IOException {

        int hours = Integer.parseInt(request.getParameter("hours"));
        int minutes = Integer.parseInt(request.getParameter("minutes"));

        int seconds = (hours * 3600) + (minutes * 60);

        response.setContentType("text/html");

        PrintWriter out = response.getWriter();

        out.println("<html><body>");
        out.println("<h2>Total Seconds = " + seconds + "</h2>");
        out.println("</body></html>");
    }
}





<web-app xmlns="http://xmlns.jcp.org/xml/ns/javaee"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="
         http://xmlns.jcp.org/xml/ns/javaee
         http://xmlns.jcp.org/xml/ns/javaee/web-app_3_1.xsd"
         version="3.1">

    <servlet>
        <servlet-name>TimeServlet</servlet-name>
        <servlet-class>TimeServlet</servlet-class>
    </servlet>

    <servlet-mapping>
        <servlet-name>TimeServlet</servlet-name>
        <url-pattern>/convert</url-pattern>
    </servlet-mapping>

</web-app>
