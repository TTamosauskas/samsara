from pathlib import Path
import re

JS = Path('src/js/07-reading-voice-bootstrap.part.js')
CSS = Path('assets/css/styles.css')

js = JS.read_text()
css = CSS.read_text()

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 target, got {count}')
    return text.replace(old, new, 1)

js = replace_once(
    js,
    "let voiceScheduleTimer=null,voiceObserver=null,voiceSpeechBusy=false,voiceDeferredListen=null,readingMicPermission=null,readingMicPermissionDenied=false;",
    "let voiceScheduleTimer=null,voiceObserver=null,voiceSpeechBusy=false,voiceDeferredListen=null,readingMicPermission=null,readingMicPermissionDenied=false,readingMicPermissionPromise=null,voiceMicStarting=false,voiceListenToken=0;",
    'voice runtime state'
)

old_sync = "function syncVoiceUi(){const enabled=!!appState.readingAssistEnabled&&!!appState.readingAssistReady&&!appState.editor,listening=enabled&&!!appState.voiceListening,speaking=enabled&&!!appState.voiceSpeaking;document.body.classList.toggle('reading-assist-enabled',enabled);document.body.classList.toggle('voice-speaking',speaking);document.body.classList.toggle('voice-listening',listening);const b=el('voiceFloatBtn');if(b){b.hidden=!enabled;b.textContent=listening?'🎙️':speaking?'🔊':'🗣️';b.setAttribute('aria-pressed',listening?'true':'false');b.setAttribute('aria-label',listening?'Ouvindo. Toque para cancelar':speaking?'Lendo. Toque para interromper':'Falar agora');b.title=b.getAttribute('aria-label');}const t=el('settingsReadingAssist');if(t)t.checked=!!appState.readingAssistEnabled;applyMusicVolume(1);}"
new_sync = "function syncVoiceUi(){const enabled=!!appState.readingAssistEnabled&&!!appState.readingAssistReady&&!appState.editor,listening=enabled&&!!appState.voiceListening,speaking=enabled&&!!appState.voiceSpeaking,starting=enabled&&!!voiceMicStarting&&!listening&&!speaking,state=listening?'listening':speaking?'speaking':starting?'starting':'idle';document.body.classList.toggle('reading-assist-enabled',enabled);document.body.classList.toggle('voice-speaking',speaking);document.body.classList.toggle('voice-listening',listening);document.body.classList.toggle('voice-mic-starting',starting);const b=el('voiceFloatBtn');if(b){b.hidden=!enabled;b.dataset.voiceState=state;b.textContent=listening?'🎙️':speaking?'🔊':starting?'🎙️':'🗣️';b.setAttribute('aria-pressed',listening||starting?'true':'false');b.setAttribute('aria-label',listening?'Ouvindo. Toque para cancelar':speaking?'Lendo em voz alta':starting?'Abrindo microfone':'Leitura por voz pronta. Toque para falar');b.title=b.getAttribute('aria-label');}const t=el('settingsReadingAssist');if(t)t.checked=!!appState.readingAssistEnabled;applyMusicVolume(1);}"
js = replace_once(js, old_sync, new_sync, 'voice UI state')

old_perm = "async function ensureReadingMicrophonePermission(){if(readingMicPermission===true)return true;if(readingMicPermissionDenied)return false;if(!navigator.mediaDevices?.getUserMedia)return true;try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});stream.getTracks().forEach(t=>t.stop());readingMicPermission=true;return true;}catch{readingMicPermissionDenied=true;toast('Permita o uso do microfone para responder por voz.');return false;}}"
new_perm = "async function ensureReadingMicrophonePermission(){if(readingMicPermission===true)return true;if(readingMicPermissionDenied)return false;if(readingMicPermissionPromise)return readingMicPermissionPromise;if(!navigator.mediaDevices?.getUserMedia)return true;readingMicPermissionPromise=(async()=>{try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});stream.getTracks().forEach(t=>t.stop());readingMicPermission=true;return true;}catch{readingMicPermissionDenied=true;toast('Permita o uso do microfone para responder por voz.');return false;}finally{readingMicPermissionPromise=null;}})();return readingMicPermissionPromise;}"
js = replace_once(js, old_perm, new_perm, 'microphone permission')

old_cancel = "function cancelVoiceRecognition(){const rec=appState.voiceRecognition;appState.voiceRecognition=null;appState.voiceListening=false;if(rec){try{rec.abort();}catch{}}syncVoiceUi();}"
new_cancel = "function cancelVoiceRecognition(){voiceListenToken++;voiceMicStarting=false;const rec=appState.voiceRecognition;appState.voiceRecognition=null;appState.voiceListening=false;if(rec){try{rec.abort();}catch{}}syncVoiceUi();}"
js = replace_once(js, old_cancel, new_cancel, 'recognition cancellation')

js = replace_once(
    js,
    "appState.voiceSpeaking||appState.voiceListening||voiceSpeechBusy)return;",
    "appState.voiceSpeaking||appState.voiceListening||voiceMicStarting||appState.voiceRecognition||voiceSpeechBusy)return;",
    'voice cycle mic guard'
)

js = replace_once(js, "startVoiceListening([],surface.key,surface);return;", "await startVoiceListening([],surface.key,surface);return;", 'answer microphone await')
js = replace_once(js, "if(appState.readingAssistEnabled&&surface.actions.length)startVoiceListening(surface.actions,surface.key);}", "if(appState.readingAssistEnabled&&surface.actions.length)await startVoiceListening(surface.actions,surface.key);}", 'surface microphone await')

pattern = r"^  function startVoiceListening\(actions=\[\],contextKey='',answerSurface=null\)\{.*\}$"
new_start = """  async function startVoiceListening(actions=[],contextKey='',answerSurface=null){
    if(!appState.readingAssistEnabled||!appState.voiceEnabled)return false;
    if(appState.voiceSpeaking||voiceSpeechBusy){voiceDeferredListen={actions,contextKey,answerSurface};return false;}
    const Ctor=voiceRecognitionCtor();
    if(!Ctor){voiceMicStarting=false;syncVoiceUi();toast('Este navegador não oferece reconhecimento de voz.');return false;}
    cancelVoiceRecognition();
    const token=voiceListenToken;
    voiceMicStarting=true;
    syncVoiceUi();
    const permitted=await ensureReadingMicrophonePermission();
    if(!permitted||token!==voiceListenToken||!appState.readingAssistEnabled||!appState.voiceEnabled||appState.voiceSpeaking||voiceSpeechBusy||contextKey!==appState.voiceContextKey){voiceMicStarting=false;syncVoiceUi();return false;}
    const rec=new Ctor();
    appState.voiceRecognition=rec;
    try{rec.lang='pt-BR';rec.continuous=false;rec.interimResults=false;rec.maxAlternatives=1;}catch{}
    let handled=false;
    rec.onstart=()=>{if(token!==voiceListenToken||appState.voiceRecognition!==rec)return;voiceMicStarting=false;appState.voiceListening=true;syncVoiceUi();};
    rec.onresult=e=>{handled=true;voiceMicStarting=false;appState.voiceListening=false;syncVoiceUi();const transcript=e.results?.[0]?.[0]?.transcript?.trim?.()||'';if(answerSurface)handleVoiceAnswerTranscript(transcript,answerSurface);else handleVoiceTranscript(transcript,actions);};
    rec.onnomatch=()=>{handled=true;voiceMicStarting=false;appState.voiceListening=false;syncVoiceUi();handleVoiceTranscript('',actions);};
    rec.onerror=e=>{handled=true;voiceMicStarting=false;appState.voiceListening=false;syncVoiceUi();const code=String(e?.error||'');if(/not-allowed|service-not-allowed/.test(code)){readingMicPermissionDenied=true;toast('Permita o uso do microfone para responder por voz.');return;}if(!/aborted/.test(code))setTimeout(()=>{if(appState.readingAssistEnabled&&token===voiceListenToken)startVoiceListening(actions,contextKey,answerSurface);},300);};
    rec.onend=()=>{if(appState.voiceRecognition===rec)appState.voiceRecognition=null;const wasListening=!!appState.voiceListening;voiceMicStarting=false;appState.voiceListening=false;syncVoiceUi();if(!handled&&wasListening&&appState.readingAssistEnabled&&token===voiceListenToken)setTimeout(()=>startVoiceListening(actions,contextKey,answerSurface),260);};
    setTimeout(()=>{if(!appState.readingAssistEnabled||token!==voiceListenToken||contextKey!==appState.voiceContextKey||appState.voiceRecognition!==rec){voiceMicStarting=false;syncVoiceUi();try{rec.abort();}catch{}return;}try{rec.start();}catch{voiceMicStarting=false;appState.voiceListening=false;if(appState.voiceRecognition===rec)appState.voiceRecognition=null;syncVoiceUi();toast('O microfone ficou indisponível.');}},120);
    return true;
  }"""
js, count = re.subn(pattern, new_start, js, count=1, flags=re.M)
if count != 1:
    raise SystemExit(f'startVoiceListening: expected 1 target, got {count}')

js = replace_once(
    js,
    "if(appState.voiceListening){cancelVoiceRecognition();return;}",
    "if(appState.voiceListening||voiceMicStarting){cancelVoiceRecognition();return;}",
    'manual microphone toggle'
)

js = replace_once(
    js,
    "readingState:()=>({enabled:!!appState.readingAssistEnabled,ready:!!appState.readingAssistReady,voiceEnabled:!!appState.voiceEnabled,combatMode:appState.combatMode,hideDiceRolls:!!appState.hideDiceRolls,sectionId:appState.sectionId||'',sectionCount:appState.book?.order?.length||0}),",
    "readingState:()=>({enabled:!!appState.readingAssistEnabled,ready:!!appState.readingAssistReady,voiceEnabled:!!appState.voiceEnabled,speaking:!!appState.voiceSpeaking,listening:!!appState.voiceListening,micStarting:!!voiceMicStarting,recognitionActive:!!appState.voiceRecognition,combatMode:appState.combatMode,hideDiceRolls:!!appState.hideDiceRolls,sectionId:appState.sectionId||'',sectionCount:appState.book?.order?.length||0}),",
    'reading test state'
)

css = replace_once(
    css,
    "body:not(.audio-mode) .voice-header-btn,body:not(.audio-mode) .voice-float-btn,body:not(.audio-mode) .voice-discovery-hint{display:none!important}",
    "body:not(.audio-mode) .voice-header-btn,body:not(.audio-mode) .voice-discovery-hint{display:none!important}",
    'legacy audio float hide'
)
css = replace_once(
    css,
    "body.reading-assist-enabled:not(.editor):not(.adventure-ended) .voice-float-btn{display:grid}",
    "body.reading-assist-enabled:not(.editor) .voice-float-btn{display:grid!important}",
    'reading float visibility'
)
css = replace_once(
    css,
    "body.voice-listening .voice-float-btn{background:color-mix(in srgb,var(--accent-soft) 84%,#fff);box-shadow:0 0 0 6px color-mix(in srgb,var(--accent) 18%,transparent),0 10px 28px rgba(20,18,28,.24)}",
    "body.voice-mic-starting .voice-float-btn{animation:voiceListenPulse .82s ease-in-out infinite;opacity:.82;background:color-mix(in srgb,var(--accent-soft) 74%,#fff);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 12%,transparent),0 10px 28px rgba(20,18,28,.24)}\n  body.voice-listening .voice-float-btn{animation:voiceListenPulse .82s ease-in-out infinite;background:color-mix(in srgb,var(--accent-soft) 84%,#fff);box-shadow:0 0 0 6px color-mix(in srgb,var(--accent) 18%,transparent),0 10px 28px rgba(20,18,28,.24)}",
    'microphone visual state'
)

JS.write_text(js)
CSS.write_text(css)
