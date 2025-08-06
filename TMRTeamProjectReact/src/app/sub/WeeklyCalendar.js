"use client";

import {DateCalendar, PickersDay, LocalizationProvider} from '@mui/x-date-pickers';
import {AdapterDateFns} from '@mui/x-date-pickers/AdapterDateFns';
import koLocale from 'date-fns/locale/ko'; // 한국어 달력 원할 경우
import {isWithinInterval} from 'date-fns';
import {useState, useEffect} from "react";


function getWeeksOfMonth(year, month) {
    const weeks = [];
    const date = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0).getDate();


    let weekStart = 1;

    while (weekStart <= lastDay) {
        const startDate = new Date(year, month - 1, weekStart);
        const startDay = startDate.getDay();
        const endDate = new Date(year, month - 1, Math.min(weekStart + (6 - startDay), lastDay));
        weeks.push({start: startDate, end: endDate});
        weekStart = endDate.getDate() + 1;
    }
    return weeks;
}

const WeekHighlightDay = (props) => {
    const {day, selectedWeekRange = {}, ...other} = props;
    const isInSelectedWeek = isWithinInterval(day, {
        start: selectedWeekRange.start,
        end: selectedWeekRange.end,
    });

    return (
        <PickersDay
            {...other}
            day={day}
            sx={{
                backgroundColor: isInSelectedWeek ? '#90caf9' : undefined,
                borderRadius: '8px',
            }}
        />
    );
};
const WeeklyCalendar = ({year, month, weekInMonth}) => {
    const selectedWeekRange = getWeeksOfMonth(year, month)[weekInMonth - 1];

    return (
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={koLocale}>
            <DateCalendar
                key={`${year}-${month}`} // ✅ key로 강제 재마운트 → 월 이동
                value={null}             // ✅ 선택된 날짜 없음
                defaultCalendarMonth={new Date(year, month - 1)} // ✅ 표시할 월 지정
                views={['day']}
                disableHighlightToday
                minDate={new Date(year, month - 1, 1)}
                maxDate={new Date(year, month - 1, new Date(year, month, 0).getDate())}
                slots={{
                    day: (dayProps) => (
                        <WeekHighlightDay
                            {...dayProps}
                            selectedWeekRange={selectedWeekRange}
                        />
                    ),
                }}
            />
        </LocalizationProvider>
    );
};

export default WeeklyCalendar;
