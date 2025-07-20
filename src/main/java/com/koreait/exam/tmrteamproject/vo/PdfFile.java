package com.koreait.exam.tmrteamproject.vo;

import lombok.*;

import javax.persistence.*;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Table(name="pdf_files")
@Builder
public class PdfFile {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "region_name", length = 100)
    private String regionName;

    @Column(name = "upjong_type", length = 100)
    private String upjongType;

    private String fileName;

    @Lob
    @Column(columnDefinition = "LONGBLOB")
    private byte[] fileData;
}
