import React, { useRef } from "react";
import { useQueryString } from "../../hooks/useQueryString";
import Button from '../Button/Button'
import Icon from '../Icon'
import Tooltiped from '../Tooltiped/Tooltiped'

import {
    FaArchive,
    FaBiohazard,
} from "react-icons/fa";
import { Modal } from "react-overlays";
import AddonModal from "../AddonModal/AddonModal";
import './AddonCard.sass';

function BackDrop(props) {
    return <div className="BackDrop" {...props}></div>
}

function formatStrings(strings) {
    if (strings.length === 0) return "";
    else if (strings.length === 1) return strings[0]
    else if (strings.length === 2) return `${strings[0]} and ${strings[1]}`
    else return `${strings.slice(0, -1).join(', ')} and ${strings[strings.length - 1]}`
}

function AddonCard({ addon }) {
    const [activeAddon, setActiveAddon] = useQueryString("addon", null);
    const active = activeAddon === addon.id
    const ref = useRef(null);

    function onActive() {
        setActiveAddon(addon.id)
    }

    // eslint-disable-next-line
    if (!addon || addon == undefined || typeof addon !== "object" || addon.id == undefined) return <></>

    try {
        return <div className={"AddonCard appear" + (active ? " active" : " inactive")} ref={ref}>
            <Modal
                show={active}
                onHide={() => {setActiveAddon(null)}}
                renderBackdrop={BackDrop}
                aria-labelledby="modal-label"
            >
                <AddonModal addon={addon} onHide={() => {setActiveAddon(null)}} />
            </Modal>

            <div className="Line">
                <Icon src={addon.icon} />
                <div className="Col AddonName">
                    <h3>
                        {addon.name}
                    </h3>
                    {(addon.authors && addon.authors.length > 0) &&
                        <span> by {formatStrings(addon.authors)}</span>
                    }
                    {addon.mc_version &&
                        <span className="McVersion"> for {addon.mc_version}</span>
                    }
                </div>
            </div>
            {!active &&
                <div className="Line">
                    {!addon.verified &&
                        <div className="Status">
                            <Tooltiped tooltip="Unverified addon. May contain malware. Proceed with caution!">
                                <FaBiohazard color="#BF616A" />
                            </Tooltiped>
                        </div>
                    }
                    {addon.status.archived &&
                        <div className="Status">
                            <Tooltiped tooltip="Addon is archived and read only">
                                <FaArchive color="#BF616A" />
                            </Tooltiped>
                        </div>
                    }
                </div>
            }
            <p>
                {addon.summary || ""}
            </p>
            {!active &&
                <div className="bottom">
                    <Button onClick={onActive}>More</Button>
                </div>
            }
        </div>
    } catch { // this is how i check for errors in json :troll:
        return <></>
    }

}

export default AddonCard;
