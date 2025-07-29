"use client";

import Script from "next/script";
import { useEffect, useRef, useState } from "react";

const LocationSelectPage = ({ onSelect }) => {
    const mapRef = useRef(null);
    const [scriptLoaded, setScriptLoaded] = useState(false);
    const [selectedInfo, setSelectedInfo] = useState(null);
    const currentPolygon = useRef(null);
    const emdPolygons = useRef([]);
    const overlayList = useRef([]);

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

            fetch("/seoul_emds.geojson")
                .then((res) => res.json())
                .then((geojson) => {
                    geojson.features.forEach((feature) => {
                        const name = feature.properties.ADSTRD_NM;
                        const coords =
                            feature.geometry.type === "Polygon"
                                ? [feature.geometry.coordinates]
                                : feature.geometry.coordinates;

                        coords.forEach((polygonCoords) => {
                            const path = polygonCoords[0].map(
                                (c) => new kakao.maps.LatLng(c[1], c[0])
                            );

                            // 기본 guide polygon (dash, no fill)
                            const polygon = new kakao.maps.Polygon({
                                path,
                                strokeWeight: 2,
                                strokeColor: "#004c80",
                                strokeOpacity: 0.8,
                                strokeStyle: "dash",
                                fillColor: "#00a0e9",
                                fillOpacity: 0,
                            });
                            polygon.setMap(map);

                            // 중심 좌표 계산
                            const latSum = path.reduce((sum, p) => sum + p.getLat(), 0);
                            const lngSum = path.reduce((sum, p) => sum + p.getLng(), 0);
                            const center = new kakao.maps.LatLng(
                                latSum / path.length,
                                lngSum / path.length
                            );

                            // 라벨 오버레이
                            const label = document.createElement("div");
                            label.innerText = name;
                            label.style.cssText = `
                                background: white;
                                border: 1px solid #444;
                                padding: 2px 6px;
                                font-size: 12px;
                                border-radius: 4px;
                              `;

                            const overlay = new kakao.maps.CustomOverlay({
                                content: label,
                                position: center,
                                yAnchor: 1,
                                zIndex: 3,
                            });
                            overlay.setMap(map);
                            overlayList.current.push(overlay);

                            // 클릭 이벤트
                            kakao.maps.event.addListener(polygon, "click", () => {
                                if (currentPolygon.current) {
                                    currentPolygon.current.setOptions({ fillOpacity: 0.01 });
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
                            });

                            emdPolygons.current.push(polygon);
                        });
                    });
                });
        });
    }, [scriptLoaded]);

    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <Script
                src={`https://dapi.kakao.com/v2/maps/sdk.js?appkey=819000337dba5ebac1dbf7847f383c66&autoload=false&libraries=services`}
                strategy="afterInteractive"
                onLoad={() => setScriptLoaded(true)}
            />

            <h1 className="tw-text-3xl tw-font-bold tw-mb-4">📍 창업 지역 선택</h1>
            <div id="map" className="tw-w-full tw-max-w-4xl tw-h-[500px] tw-mb-6 tw-border tw-rounded-lg" />

            {selectedInfo && (
                <div className="tw-text-center tw-mb-6">
                    <p className="tw-text-lg">선택된 행정동: {selectedInfo.address}</p>
                </div>
            )}

            <button
                onClick={() => selectedInfo && onSelect(selectedInfo)}
                disabled={!selectedInfo}
                className="tw-bg-blue-500 tw-text-white tw-px-6 tw-py-2 tw-rounded-xl hover:tw-bg-blue-600 tw-transition disabled:tw-bg-gray-400"
            >
                이 위치 선택 →
            </button>
        </div>
    );
};

export default LocationSelectPage;
