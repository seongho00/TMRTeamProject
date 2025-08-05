package com.ltk.TMR.entity;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

import java.io.IOException;
import java.util.Collections;
import java.util.List;

@Converter
public class AttachmentDtoListConverter implements AttributeConverter<List<LhApplyInfo.AttachmentDto>, String> {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(List<LhApplyInfo.AttachmentDto> attribute) {
        // 객체 리스트를 JSON 문자열로 변환
        if (attribute == null || attribute.isEmpty()) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(attribute);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("JSON writing error", e);
        }
    }

    @Override
    public List<LhApplyInfo.AttachmentDto> convertToEntityAttribute(String dbData) {
        // JSON 문자열을 객체 리스트로 변환
        if (dbData == null || dbData.isEmpty()) {
            return Collections.emptyList();
        }
        try {
            return objectMapper.readValue(dbData, new TypeReference<>() {});
        } catch (IOException e) {
            throw new IllegalArgumentException("JSON reading error", e);
        }
    }
}