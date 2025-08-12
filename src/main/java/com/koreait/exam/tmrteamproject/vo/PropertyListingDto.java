package com.koreait.exam.tmrteamproject.vo;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class PropertyListingDto {
    private String title;
    private String tradeType;
    private String price;
    private String type;
    private String spec;
    private String description;
    private String tags;
    private String imageUrl;
}