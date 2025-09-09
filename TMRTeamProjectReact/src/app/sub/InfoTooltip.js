import { useState } from "react";
import IconButton from '@mui/material/IconButton';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';


function InfoTooltip({ text }) {
    const [open, setOpen] = useState(false);

    return (
        <div className="tw-relative tw-inline-block">
            <IconButton aria-label="설명 보기">
                <HelpOutlineIcon onClick={() => setOpen(!open)}/>
            </IconButton>

            {/* 설명 박스 */}
            {open && (
                <div
                    className="tw-absolute tw-left-1/2 tw-top-full tw-mt-1 tw-w-56
                     tw-bg-black tw-text-white tw-text-xs tw-rounded-lg tw-px-2 tw-py-1
                     tw-transform tw--translate-x-1/2 tw-shadow-lg z-10"
                >
                    {text}
                </div>
            )}
        </div>
    );
}

export default InfoTooltip;
