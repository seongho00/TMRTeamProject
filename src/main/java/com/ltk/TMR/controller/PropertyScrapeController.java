package com.ltk.TMR.controller;

import com.ltk.TMR.vo.PropertyListingDto;
import com.ltk.TMR.service.PropertyScrapingService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class PropertyScrapeController {

    private final PropertyScrapingService propertyScrapingService;

    @GetMapping("/properties")
    public ResponseEntity<List<PropertyListingDto>> scrapeProperties(@RequestParam("dongCode") String dongCode) {
        List<PropertyListingDto> properties = propertyScrapingService.getProperties(dongCode);
        return ResponseEntity.ok(properties);
    }
}