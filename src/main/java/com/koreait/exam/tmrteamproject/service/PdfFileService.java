package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.PdfFileRepository;
import com.koreait.exam.tmrteamproject.vo.PdfFile;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.File;
import java.nio.file.Files;
import java.util.Arrays;

@Service
@RequiredArgsConstructor
public class PdfFileService {

    private final PdfFileRepository pdfFileRepository;

    @Async
    public void savePdfsAsync(String folderPath) {
        long savedCount = pdfFileRepository.count();
        if (savedCount >= 246 * 3) {
            System.out.println("이미 저장 완료된 상태 (총 " + savedCount + "개), 실행 중단.");
            return;
        }

        File folder = new File(folderPath);
        if (!folder.exists() || !folder.isDirectory()) {
            System.err.println("폴더가 존재하지 않거나 디렉토리가 아닙니다: " + folderPath);
            return;
        }

        File[] files = folder.listFiles((dir, name) -> name.toLowerCase().endsWith(".pdf"));
        if (files == null || files.length == 0) {
            System.out.println("PDF 파일이 없습니다.");
            return;
        }

        int count = 0;
        for (File file : files) {
            if (count >= 246 * 3) {
                System.out.println("246 * 3개 초과, 생략됨: " + file.getName());
                break;
            }

            try {
                if (pdfFileRepository.existsByFileName(file.getName())) {
                    System.out.println("이미 저장됨: " + file.getName());
                    continue;
                }

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
                count++;

            } catch (Exception e) {
                System.err.println("저장 실패: " + file.getName());
                e.printStackTrace();
            }
        }

        System.out.println("총 저장 완료 수: " + count);
        System.out.println("비동기 PDF 저장 작업 완료 (총 " + count + "개)");
    }
}
