"use client";

import Script from "next/script";
import React, {useEffect, useRef, useState} from "react";
import LocationDetailPanel from "./LocationDetailPanel";


const LocationSelectPage = ({onSelect, onBack}) => {
    const mapRef = useRef(null);
    const [scriptLoaded, setScriptLoaded] = useState(false);
    const [selectedInfo, setSelectedInfo] = useState(null);
    const currentPolygon = useRef(null);
    const emdPolygons = useRef([]);
    const overlayList = useRef([]);
    const currentOverlay = useRef(null); // 오버레이 1개만 유지
    const [detailInfo, setDetailInfo] = useState(null);

    useEffect(() => {
        if (!scriptLoaded || !window.kakao) return;

        kakao.maps.load(() => {
            const container = document.getElementById("map");
            const options = {
                center: new kakao.maps.LatLng(37.5665, 126.9780),
                level: 6,
            };

            const map = new kakao.maps.Map(container, options);
            mapRef.current = map;

            clearPolygons();
            loadAndDrawPolygons(map.getLevel(), map);

            kakao.maps.event.addListener(map, "zoom_changed", () => {
                const level = map.getLevel();
                console.log("Zoom level changed:", level);
                clearPolygons();
                loadAndDrawPolygons(level, map);
            });


        });
    }, [scriptLoaded]);

    function loadAndDrawPolygons(level, map) {
        const isSggLevel = level >= 7;
        const url = isSggLevel ? "/seoul_sggs.geojson" : "/seoul_emds.geojson";

        fetch(url)
            .then((res) => res.json())
            .then((geojson) => {
                geojson.features.forEach((feature) => {
                    const name = isSggLevel
                        ? feature.properties.SIGUNGU_NM
                        : feature.properties.ADSTRD_NM;

                    const coords =
                        feature.geometry.type === "Polygon"
                            ? [feature.geometry.coordinates]
                            : feature.geometry.coordinates;

                    coords.forEach((polygonCoords) => {
                        const path = polygonCoords[0].map(
                            (c) => new kakao.maps.LatLng(c[1], c[0])
                        );

                        const polygon = new kakao.maps.Polygon({
                            path,
                            strokeWeight: 2,
                            strokeColor: "#004c80",
                            strokeOpacity: 0.8,
                            strokeStyle: "dash",
                            fillColor: "#00a0e9",
                            fillOpacity: 0.01,
                        });

                        polygon.setMap(map);
                        emdPolygons.current.push(polygon);

                        // 중심 좌표 계산
                        const latSum = path.reduce((sum, p) => sum + p.getLat(), 0);
                        const lngSum = path.reduce((sum, p) => sum + p.getLng(), 0);
                        const center = new kakao.maps.LatLng(
                            latSum / path.length,
                            lngSum / path.length
                        );

                        // 라벨
                        const label = document.createElement("div");
                        label.innerText = name;
                        label.style.cssText = `
                            background: white;
                            border: 1px solid #444;
                            padding: 2px 6px;
                            font-size: 12px;
                            border-radius: 4px;
                            pointer-events: none;
                        `;

                        label.className = "custom-overlay";

                        const overlay = new kakao.maps.CustomOverlay({
                            content: label,
                            position: center,
                            yAnchor: 1,
                            zIndex: 3,
                        });
                        overlay.setMap(map);
                        overlayList.current.push(overlay);

                        // 클릭 이벤트 (only for 행정동)
                        if (!isSggLevel) {
                            kakao.maps.event.addListener(polygon, "click", () => {
                                const isAlreadySelected = currentPolygon.current === polygon;
                                if (currentOverlay.current) {
                                    currentOverlay.current.setMap(null);
                                }

                                const emdCode = feature.properties.ADSTRD_CD;

                                fetch(`http://localhost:8080/usr/commercialData/findByEmdCode?emdCode=${emdCode}`)
                                    .then(res => {
                                        if (!res.ok) {
                                            throw new Error("데이터 없음");
                                        }
                                        return res.json();
                                    })
                                    .then(data => {
                                        // ✅ 정상 응답 처리
                                        const totalFloating = data.total;
                                        const totalWorkers = data.workingTotal;
                                        const ageMap = {
                                            "10대": data.age10,
                                            "20대": data.age20,
                                            "30대": data.age30,
                                            "40대": data.age40,
                                            "50대": data.age50,
                                            "60대 이상": data.age60plus,
                                        };

                                        const dominantAge = Object.entries(ageMap)
                                            .sort((a, b) => b[1] - a[1])[0][0];  // 수치가 가장 큰 연령대 키 추출

                                        // 오버레이 content DOM 생성
                                        const content = document.createElement("div");
                                        content.innerHTML = `
                                            <div style="
                                              background: white;
                                              border: 1px solid #333;
                                              border-radius: 8px;
                                              padding: 8px 12px;
                                              font-size: 13px;
                                              box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                                              max-width: 240px;
                                            ">
                                              <strong>${name}</strong><br/>
                                              👥 유동인구: ${totalFloating.toLocaleString()}<br/>
                                              🧑‍💼 직장인구: ${totalWorkers.toLocaleString()}<br/>
                                              🎯 연령대: ${dominantAge}<br/>
                                              <button id="detail-button" style="
                                                  margin-top: 6px;
                                                  background: #3182ce;
                                                  color: white;
                                                  border: none;
                                                  padding: 4px 8px;
                                                  font-size: 12px;
                                                  border-radius: 4px;
                                                  cursor: pointer;
                                                ">상세보기</button>
                                            </div>
                                        `;

                                        // 오버레이 생성 및 표시
                                        const overlay = new kakao.maps.CustomOverlay({
                                            content,
                                            position: center,
                                            yAnchor: 1.2,
                                            zIndex: 10,
                                        });
                                        overlay.setMap(map);
                                        currentOverlay.current = overlay;

                                        // 상세보기 버튼 활성화
                                        document.getElementById("detail-button").addEventListener("click", () => {
                                            console.log("detail")
                                            setDetailInfo({
                                                address: emdCode,
                                            });
                                        });

                                    })
                                    .catch(err => {
                                        console.error("에러 발생:", err);
                                    });


                                if (isAlreadySelected) {
                                    // 선택 해제
                                    polygon.setOptions({
                                        strokeStyle: "dash",
                                        strokeColor: "#004c80",
                                        fillColor: "#00a0e9",
                                        fillOpacity: 0.01,
                                    });
                                    currentPolygon.current = null;
                                    setSelectedInfo(null);

                                } else {
                                    // 새 polygon 선택
                                    if (currentPolygon.current) {
                                        currentPolygon.current.setOptions({
                                            strokeStyle: "dash",
                                            fillOpacity: 0.01,
                                        });
                                    }
                                    polygon.setOptions({
                                        strokeStyle: "solid",
                                        fillOpacity: 0.3,
                                    });
                                    currentPolygon.current = polygon;

                                    setSelectedInfo({
                                        address: name,
                                        path,
                                        levelType: isSggLevel ? "sgg" : "emd",
                                    });
                                    if (currentPolygon.current) {
                                        currentPolygon.current.setOptions({fillOpacity: 0.01});
                                    }

                                    polygon.setOptions({
                                        strokeStyle: "solid",
                                        fillOpacity: 0.3,
                                    });
                                    currentPolygon.current = polygon;

                                    setSelectedInfo({
                                        address: name,
                                        path,
                                    });
                                }

                            });
                        }
                    });
                });
            });
    }

    function clearPolygons() {
        emdPolygons.current.forEach((p) => p.setMap(null));
        emdPolygons.current = [];
        overlayList.current.forEach((o) => o.setMap(null));
        overlayList.current = [];
        currentPolygon.current = null;
    }


    return (

        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <Script
                src={`https://dapi.kakao.com/v2/maps/sdk.js?appkey=819000337dba5ebac1dbf7847f383c66&autoload=false&libraries=services`}
                strategy="afterInteractive"
                onLoad={() => setScriptLoaded(true)}
            />

            <h1 className="tw-text-3xl tw-font-bold tw-mb-4">📍 창업 지역 선택</h1>
            <div id="map" className="tw-w-full tw-max-w-4xl tw-h-[500px] tw-mb-6 tw-border tw-rounded-lg"/>

            {selectedInfo && (
                <div className="tw-text-center tw-mb-6">
                    <p className="tw-text-lg">선택된 행정동: {selectedInfo.address}</p>
                </div>
            )}

            <button
                onClick={() => {
                    if (selectedInfo) onSelect(selectedInfo);
                }}
                disabled={!selectedInfo}
                className="tw-bg-blue-500 tw-text-white tw-px-6 tw-py-2 tw-rounded-xl hover:tw-bg-blue-600 tw-transition disabled:tw-bg-gray-400"
            >
                이 위치 선택 →
            </button>
            <button
                onClick={onBack}
                className="tw-absolute tw-top-6 tw-left-6 tw-bg-gray-200 tw-text-gray-800 tw-px-4 tw-py-2 tw-rounded-md hover:tw-bg-gray-300 tw-transition"
            >
                ← 이전 단계
            </button>
            {detailInfo && (
                <LocationDetailPanel
                    info={detailInfo}
                    onClose={() => setDetailInfo(null)}
                />
            )}
        </div>
    );
};

export default LocationSelectPage;
