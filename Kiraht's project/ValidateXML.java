import javax.xml.XMLConstants;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import org.xml.sax.SAXException;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Schema;
import javax.xml.validation.Validator;
import java.io.File;
import javax.xml.XMLConstants;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import java.io.File;
import javax.xml.XMLConstants;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Schema;
import javax.xml.validation.Validator;

public class ValidateXML {
    public static void main(String[] args) {
        try {
            File xmlFile = new File("C:\\CODINGS\\DBMS\\DBMS_EXE10\\students.xml");
            File xsdFile = new File("C:\\CODINGS\\DBMS\\DBMS_EXE10\\students.xsd");

            SchemaFactory factory = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);
            Schema schema = factory.newSchema(xsdFile);
            Validator validator = schema.newValidator();

            validator.validate(new StreamSource(xmlFile));

            System.out.println("XML is valid.");
        } catch (SAXException | IOException e) {
            System.out.println("Validation error: " + e.getMessage());
        }
    }
}