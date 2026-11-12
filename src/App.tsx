import { useRef, useState } from "react";
import { ArrowRight, CarFront, CloudUpload, Layers3, ScanLine, ShieldCheck, Sparkles, Trash2, X, CheckCircle2 } from "lucide-react";

type View = "Unassigned" | "Front" | "Front-left" | "Left side" | "Rear-left" | "Rear" | "Rear-right" | "Right side" | "Front-right" | "Roof" | "Interior front" | "Interior rear" | "Wheel/detail";
type Photo = { id: string; file: File; url: string; width: number; height: number; view: View };
const views: View[] = ["Unassigned", "Front", "Front-left", "Left side", "Rear-left", "Rear", "Rear-right", "Right side", "Front-right", "Roof", "Interior front", "Interior rear", "Wheel/detail"];
const exterior: View[] = ["Front", "Front-left", "Left side", "Rear-left", "Rear", "Rear-right", "Right side", "Front-right"];

export default function App() {
  const picker = useRef<HTMLInputElement>(null);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [name, setName] = useState("");
  const [kind, setKind] = useState("Passenger car");
  const [msg, setMsg] = useState("");
  const [guide, setGuide] = useState(true);

  async function add(files: FileList | File[]) {
    const accepted = Array.from(files).filter(file => ["image/jpeg", "image/png", "image/webp"].includes(file.type));
    if (accepted.length !== files.length) setMsg("Some files were skipped. Use JPG, PNG or WebP.");
    const additions: Photo[] = [];
    for (const file of accepted) {
      if (photos.some(photo => photo.file.name === file.name && photo.file.size === file.size) ||
          additions.some(photo => photo.file.name === file.name && photo.file.size === file.size)) continue;
      const url = URL.createObjectURL(file);
      const dimensions = await new Promise<{ width: number; height: number }>(resolve => {
        const image = new Image();
        image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
        image.onerror = () => resolve({ width: 0, height: 0 });
        image.src = url;
      });
      additions.push({ id: crypto.randomUUID(), file, url, ...dimensions, view: "Unassigned" });
    }
    setPhotos(current => [...current, ...additions]);
  }

  function remove(id: string) {
    setPhotos(current => {
      const photo = current.find(item => item.id === id);
      if (photo) URL.revokeObjectURL(photo.url);
      return current.filter(item => item.id !== id);
    });
  }

  function setView(id: string, view: View) {
    setPhotos(current => current.map(photo => photo.id === id ? { ...photo, view } : photo));
  }

  const covered = exterior.filter(view => photos.some(photo => photo.view === view));
  const missing = exterior.filter(view => !covered.includes(view));

  function validate() {
    if (!name.trim()) setMsg("Name this vehicle project first.");
    else if (photos.length < 12) setMsg("Add at least 12 distinct photos for the initial intake check.");
    else if (missing.length) setMsg("Assign photos to all 8 exterior angles. Missing: " + missing.join(", ") + ".");
    else if (photos.some(photo => photo.width < 1000 || photo.height < 650)) setMsg("Some images are below the initial 1000 × 650 resolution check.");
    else setMsg("Guided capture checks passed. This is not an automated photogrammetry quality assessment; secure upload and reconstruction are not connected yet.");
  }

  return (
    <div className="layout">
      <aside>
        <div className="brand"><span><ScanLine /></span><b>HACKYTECH<small>VEHICLE INTELLIGENCE</small></b></div>
        <label>WORKSPACE</label>
        <div className="nav"><Layers3 size={17} /> Vehicle projects</div>
        <div className="bottom"><p>● ENGINE WORKSPACE<small>EARLY ACCESS BUILD</small></p><b>HT　HackyTech</b></div>
      </aside>
      <main>
        <header>Workspace　/　New vehicle project <span><ShieldCheck size={14} /> Private workspace</span></header>
        <article>
          <div className="hero">
            <div>
              <small><Sparkles size={14} /> HACKYTECH VEHICLE INTELLIGENCE ENGINE</small>
              <h1>Bring a real vehicle<br /><em>into 3D.</em></h1>
              <p>Build a capture set of your actual vehicle. Track the angles you have photographed before sending it to a future reconstruction pipeline.</p>
            </div>
            <div className="car"><i /><i /><CarFront size={88} /><small>3D RECONSTRUCTION</small></div>
          </div>
          <div className="steps">
            <b>01　Capture<small>Upload overlapping photos</small></b>
            <b>02　Reconstruct<small>Build geometry and texture</small></b>
            <b>03　Customize<small>Edit materials and parts</small></b>
          </div>
          <section>
            <div className="panelhead">
              <div><small>NEW PROJECT · 01</small><h2>Vehicle capture</h2><p>Identify your vehicle, then add photographs from around it.</p></div>
              <label>DRAFT PROJECT</label>
            </div>
            <div className="fields">
              <label>PROJECT NAME<input value={name} onChange={event => setName(event.target.value)} placeholder="e.g. Toyota Corolla 2018" /></label>
              <label>VEHICLE CATEGORY<select value={kind} onChange={event => setKind(event.target.value)}>{["Passenger car", "SUV / 4×4", "Pickup truck", "Van / minibus", "Motorcycle", "Other vehicle"].map(value => <option key={value}>{value}</option>)}</select></label>
            </div>
            <div className="uploadhead">
              <div><b>Upload vehicle photographs</b><small>JPG, PNG or WebP · Multiple angles · Original resolution preferred</small></div>
              <strong>{photos.length}<small> / 12 minimum</small></strong>
            </div>
            <div className="drop" role="button" tabIndex={0}
              onClick={() => picker.current?.click()}
              onKeyDown={event => { if (event.key === "Enter" || event.key === " ") picker.current?.click(); }}
              onDragOver={event => event.preventDefault()}
              onDrop={event => { event.preventDefault(); void add(event.dataTransfer.files); }}>
              <input ref={picker} hidden type="file" multiple accept="image/jpeg,image/png,image/webp"
                onChange={event => { if (event.target.files) void add(event.target.files); event.target.value = ""; }} />
              <CloudUpload size={30} /><b>Drop vehicle photos here</b>
              <span>or <strong>browse files</strong> from your device</span>
              <small>At least 12 distinct views for the initial intake check</small>
            </div>
            {photos.length > 0 && (
              <>
                <div className="coverage">
                  <div className="coverage-head"><b>Exterior angle coverage</b><strong>{covered.length} / 8</strong></div>
                  <div className="coverage-track"><i style={{ width: (covered.length / 8 * 100) + "%" }} /></div>
                  <div className="coverage-grid">
                    {exterior.map(view => (
                      <span key={view} className={covered.includes(view) ? "done" : ""}>
                        {covered.includes(view) ? <CheckCircle2 size={13} /> : <span className="emptydot" />}
                        {view}
                      </span>
                    ))}
                  </div>
                  <small className="coverage-note">Assign each image its closest angle below. More overlapping images per angle are encouraged.</small>
                </div>
                <div className="photos">
                  {photos.map(photo => (
                    <div className="photo-card" key={photo.id}>
                      <div className="photo">
                        <img src={photo.url} alt={photo.file.name} />
                        <button onClick={() => remove(photo.id)} aria-label="Remove photo"><Trash2 size={13} /></button>
                        <small>{photo.width} × {photo.height}</small>
                      </div>
                      <label>PHOTO ANGLE
                        <select value={photo.view} onChange={event => setView(photo.id, event.target.value as View)}>
                          {views.map(view => <option key={view}>{view}</option>)}
                        </select>
                      </label>
                    </div>
                  ))}
                </div>
              </>
            )}
            {msg && <div className="notice">{msg}<button onClick={() => setMsg("")}><X size={14} /></button></div>}
            <div className="quality">●　{photos.length >= 12 && missing.length === 0 ? "Guided coverage checks met" : "Capture set incomplete"}<small>These checks do not guarantee successful reconstruction.</small></div>
            <div className="actions">
              <span><ShieldCheck size={14} /> Photos remain in this browser until secure upload is implemented.</span>
              <button onClick={validate}>Validate capture set <ArrowRight size={15} /></button>
            </div>
          </section>
          {guide && (
            <section className="guide">
              <b>How to photograph your vehicle</b><button onClick={() => setGuide(false)}><X size={14} /></button>
              <div>
                <p><strong>01 · Walk around</strong><br />Front, rear, both sides and four diagonal views.</p>
                <p><strong>02 · Overlap views</strong><br />Keep common features visible between frames.</p>
                <p><strong>03 · Capture details</strong><br />Roof, wheels, lights, windows and cabin.</p>
                <p><strong>04 · Control reflections</strong><br />Use steady lighting; avoid glare and blur.</p>
              </div>
            </section>
          )}
          <footer>HACKYTECH · BUILDING VEHICLE INTELLIGENCE <span>SELF-HOSTED ENGINE DIRECTION</span></footer>
        </article>
      </main>
    </div>
  );
}