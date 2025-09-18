package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.CommercialProperty;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CommercialPropertyRepository extends JpaRepository<CommercialProperty, Long> {

    List<CommercialProperty> findByPriceType(String priceType);
}
