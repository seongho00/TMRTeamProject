"use client";

import Script from "next/script";
import { useEffect, useRef, useState } from "react";

const LocationSelectPage = ({ onSelect }) => {
    const mapRef = useRef(null);
    const markerRef = useRef(null);
    const [selectedInfo, setSelectedInfo] = useState(null);

    const initMap = () => {
        try {
            const container = document.getElementById("map");
            if (!container) {
                console.error("❌ map div 없음");
                return;
            }

            const options = {
                center: new window.kakao.maps.LatLng(37.5665, 126.9780),
                level: 6,
            };

            const map = new window.kakao.maps.Map(container, options);
            mapRef.current = map;

            window.kakao.maps.event.addListener(map, "click", function (mouseEvent) {
                const latlng = mouseEvent.latLng;

                if (markerRef.current) markerRef.current.setMap(null);

                const marker = new window.kakao.maps.Marker({ position: latlng });
                marker.setMap(map);
                markerRef.current = marker;

                const geocoder = new window.kakao.maps.services.Geocoder();
                geocoder.coord2Address(latlng.getLng(), latlng.getLat(), function (result, status) {
                    if (status === window.kakao.maps.services.Status.OK) {
                        const address = result[0].address.address_name;
                        setSelectedInfo({
                            lat: latlng.getLat(),
                            lng: latlng.getLng(),
                            address: address,
                        });
                    }
                });
            });

            console.log("✅ 지도 초기화 완료");
        } catch (err) {
            console.error("❌ 지도 초기화 실패", err);
        }
    };

    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <Script
                src={`https://dapi.kakao.com/v2/maps/sdk.js?appkey=819000337dba5ebac1dbf7847f383c66&autoload=false&libraries=services`}
                strategy="afterInteractive"
                onLoad={() => {
                    console.log("✅ Kakao Maps SDK 로드됨");
                    if (window.kakao && window.kakao.maps) {
                        window.kakao.maps.load(() => {
                            initMap();
                        });
                    } else {
                        console.error("❌ window.kakao 또는 maps가 없음");
                    }
                }}
                onError={() => console.error("❌ Kakao Maps SDK 로드 실패")}
            />

            <h1 className="tw-text-3xl tw-font-bold tw-mb-4">📍 창업 지역 선택</h1>
            <div id="map" className="tw-w-full tw-max-w-4xl tw-h-[500px] tw-mb-6 tw-border tw-rounded-lg" />

            {selectedInfo && (
                <div className="tw-text-center tw-mb-6">
                    <p className="tw-text-lg">선택된 위치: {selectedInfo.address}</p>
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
