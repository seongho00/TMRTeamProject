package com.koreait.exam.tmrteamproject.service;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.rendering.PDFRenderer;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

@Service
public class MarketAreaService {

    String fileName = "C:/Users/user/Desktop/TeamProject/TMRTeamProject/src/main/java/com/koreait/exam/tmrteamproject/service/대전광역시 대덕구 회덕동 족발_보쌈.pdf";

    public String getPdfRead() {
        File file = new File(fileName);

        try(PDDocument document = Loader.loadPDF(file)) {
            PDFTextStripper stripper = new PDFTextStripper();
            String text = stripper.getText(document);
            return text;
        }
        catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public List<String> extractImagesFromPdf() {
        List<String> base64Images = new ArrayList<>();

        try (PDDocument document = Loader.loadPDF(new File(fileName))) {
            PDFRenderer pdfRenderer = new PDFRenderer(document);

            for (int i = 0; i < document.getNumberOfPages(); i++) {
                BufferedImage image = pdfRenderer.renderImageWithDPI(i, 200);
                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                ImageIO.write(image, "png", baos);

                String base64 = Base64.getEncoder().encodeToString(baos.toByteArray());
                base64Images.add("data:image/png;base64," + base64);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        return base64Images;
    }
}
