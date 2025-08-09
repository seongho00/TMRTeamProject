package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.LearningRepository;
import com.koreait.exam.tmrteamproject.vo.Learning;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.FileReader;

@Service
@RequiredArgsConstructor
public class LearningService {

    @Autowired
    private LearningRepository learningRepository;

    public void setSaved(String csvfile) {
        try {
            BufferedReader reader = new BufferedReader(new FileReader(csvfile));
            String line = null;

            // 첫줄 읽고 header라고 가정 후 버림
            reader.readLine();

            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");

                Learning data = new Learning();

                data.setYearQuarterCode(parts[0].trim());
                data.setHjd_co(parts[1].trim());
                data.setHjd_cn(parts[2].trim());

                data.setTotalFloatingPopulation(Integer.parseInt(parts[3].trim()));
                data.setMaleFloatingPopulation(Integer.parseInt(parts[4].trim()));
                data.setFemaleFloatingPopulation(Integer.parseInt(parts[5].trim()));
                data.setAge10FloatingPopulation(Integer.parseInt(parts[6].trim()));
                data.setAge20FloatingPopulation(Integer.parseInt(parts[7].trim()));
                data.setAge30FloatingPopulation(Integer.parseInt(parts[8].trim()));
                data.setAge40FloatingPopulation(Integer.parseInt(parts[9].trim()));
                data.setAge50FloatingPopulation(Integer.parseInt(parts[10].trim()));
                data.setAge60PlusFloatingPopulation(Integer.parseInt(parts[11].trim()));
                data.setFloatingPopulation_00_06(Integer.parseInt(parts[12].trim()));
                data.setFloatingPopulation_06_11(Integer.parseInt(parts[13].trim()));
                data.setFloatingPopulation_11_14(Integer.parseInt(parts[14].trim()));
                data.setFloatingPopulation_14_17(Integer.parseInt(parts[15].trim()));
                data.setFloatingPopulation_17_21(Integer.parseInt(parts[16].trim()));
                data.setFloatingPopulation_21_24(Integer.parseInt(parts[17].trim()));
                data.setMondayFloatingPopulation(Integer.parseInt(parts[18].trim()));
                data.setTuesdayFloatingPopulation(Integer.parseInt(parts[19].trim()));
                data.setWednesdayFloatingPopulation(Integer.parseInt(parts[20].trim()));
                data.setThursdayFloatingPopulation(Integer.parseInt(parts[21].trim()));
                data.setFridayFloatingPopulation(Integer.parseInt(parts[22].trim()));
                data.setSaturdayFloatingPopulation(Integer.parseInt(parts[23].trim()));
                data.setSundayFloatingPopulation(Integer.parseInt(parts[24].trim()));

                learningRepository.save(data);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
