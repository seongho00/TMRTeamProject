package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.PdfFileRepository;
import com.koreait.exam.tmrteamproject.vo.PdfFile;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Arrays;

@Service
@RequiredArgsConstructor
public class PdfFileService {

    private final PdfFileRepository pdfFileRepository;

    public void saveAllPdfsFromFolder(String folderPath) {
        File folder = new File(folderPath);

        if (!folder.exists() || !folder.isDirectory()) {
            throw new RuntimeException("폴더가 존재하지 않거나 디렉토리가 아닙니다: " + folderPath);
        }

        File[] files = folder.listFiles((dir, name) -> name.toLowerCase().endsWith(".pdf"));
        if (files == null || files.length == 0) {
            System.out.println("PDF 파일이 없습니다.");
            return;
        }

        for (File file : files) {
            try {
                boolean exists = pdfFileRepository.existsByFileName(file.getName());
                if (exists) {
                    System.out.println("이미 저장됨: " + file.getName());
                    continue;
                }

                // 예시: "대전광역시 서구 가수원동 편의점.pdf"
                String fileName = file.getName().replace(".pdf", "");
                String[] parts = fileName.split(" ");

                String regionName = parts.length >= 4 ? String.join(" ", Arrays.copyOfRange(parts, 0, parts.length - 1)) : "알수없음";
                String upjongType = parts[parts.length - 1];

                byte[] fileBytes = Files.readAllBytes(file.toPath());

                PdfFile pdfFile = PdfFile.builder()
                        .fileName(file.getName())
                        .fileData(fileBytes)
                        .regionName(regionName)
                        .upjongType(upjongType)
                        .build();

                pdfFileRepository.save(pdfFile);
                System.out.println("저장 완료: " + file.getName());

            } catch (IOException e) {
                System.err.println("저장 실패: " + file.getName());
                e.printStackTrace();
            }
        }
    }
}
