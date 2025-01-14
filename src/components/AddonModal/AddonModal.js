import React from "react";
import Button from '../Button/Button'
import Tooltiped from '../Tooltiped/Tooltiped'

import {
    FaWindowMinimize,
    FaArchive,
    FaBiohazard,
    FaDiscord,
    FaLink,
    FaGithub,
    FaDownload,
    FaVirus,
    FaStar,
    FaCalendarAlt
} from "react-icons/fa";
import moment from "moment";
import {
    GoVersions
} from "react-icons/go"
import Icon from '../Icon'

import './AddonModal.sass';

function formatStrings(strings) {
    if (strings.length === 0) return "";
    else if (strings.length === 1) return strings[0]
    else if (strings.length === 2) return `${strings[0]} and ${strings[1]}`
    else return `${strings.slice(0, -1).join(', ')} and ${strings[strings.length - 1]}`
}

function getIcon(type) {
    switch (type) {
        case "discord": return <FaDiscord />
        case "github": return <FaGithub />
        case "virustotal": return <FaVirus />
        default: return <FaLink />
    }
}

function AddonModal({ addon, onHide }) {
    return <div className={"AddonModal appear"}>
        <button className="Close" onClick={() => { onHide() }}>
            <FaWindowMinimize />
        </button>
        <div className="Line">
            <Icon src={addon.icon} />
            <div className="Col">
                <h3 id="modal-label">{addon.name}</h3>
                {(addon.authors && addon.authors.length > 0) &&
                    <span> by {formatStrings(addon.authors)}</span>
                }
            </div>
        </div>
        <div className="Col">
            {addon.mc_version &&
                <div className="Status">
                    <span>
                        <GoVersions style={{top: '2px', position: 'relative'}}/>
                        {' '}Addon avaliable for Minecraft {addon.mc_version} and possibly older
                    </span>
                </div>
            }
            {!addon.verified &&
                <div className="Status">
                    <span>
                        <FaBiohazard color="#BF616A" />
                        {' '}Unverified addon. May contain malware. Proceed with caution!</span>
                </div>
            }
            {addon.status.archived &&
                <div className="Status">
                    <span>
                        <FaArchive color="#BF616A" />
                        {' '}Addon is archived and read only
                    </span>
                </div>
            }
            {(addon.stars>0) &&
                <div className="Status">
                    <span>
                        <FaStar color="#EBCB8B" />
                        {' '} {addon.stars}{' '}Github stars
                    </span>
                </div>
            }
            {addon.last_update &&
                <div className="Status">
                    <span>
                        <FaCalendarAlt />
                        {' '}Last update:{' '}{moment.utc(addon.last_update).local().startOf('seconds').fromNow()}
                    </span>
                </div>
            }
            <hr />
        </div>
        <p>
            {addon.summary || ""}
        </p>
        {(typeof addon.features !== "undefined" && addon.features.length > 0) &&
            <section className="Features">
                <h4>Features</h4>
                <ul>
                    {(addon.features).map((feat) => {
                        return <li key={feat}>{feat}</li>
                    })}
                </ul>
            </section>
        }
        <div className="Line appear centered">
            { typeof addon.links.download === "undefined" &&
                <a href={addon.links.github} target="_blank">
                    <Button>
                        <FaGithub style={{ marginRight: '0.6rem' }} />
                        Repository
                    </Button>
                </a>
            }
            { addon.links.download &&
                <a href={addon.links.download}>
                    <Button>
                        <FaDownload style={{ marginRight: '0.6rem' }} />
                        Download
                    </Button>
                </a>
            }
            <div className="IconLinks">
                {Object.keys(addon.links).map((key) => {
                    if ((key === "github" && typeof addon.links.download === "undefined") || key === "download") return <></>
                    else {
                        return <Tooltiped key={key} tooltip={key}>
                            <a href={addon.links[key]} target="_blank">{getIcon(key)}</a>
                        </Tooltiped>
                    }
                })}
            </div>
        </div>
    </div>

}

export default AddonModal;