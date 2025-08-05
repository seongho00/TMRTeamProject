package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.PdfFile;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface PdfFileRepository extends JpaRepository<PdfFile, Long> {
    Optional<PdfFile> findByFileName(String fileName);

    boolean existsByFileName(String name);

    @Query("SELECT p.fileName FROM PdfFile p")
    List<String> findAllFileNames();
}
