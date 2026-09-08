from pathlib import Path
p=Path('src/js/07-reading-voice-bootstrap.part.js')
s=p.read_text()
old="""  async function waitVoiceActionSettlement(before,actionPromise){
    let actionDone=!(actionPromise&&typeof actionPromise.then==='function'),actionError=null;
    if(!actionDone)Promise.resolve(actionPromise).then(()=>{actionDone=true;},err=>{actionDone=true;actionError=err;console.warn('Ação do Livro iniciada por voz falhou.',err);});
    for(;;){
      const sectionChanged=appState.sectionId!==before.sectionId,currentKey=voiceSurfaceKeySafe(),surfaceChanged=!!currentKey&&currentKey!==before.surfaceKey;
      if(sectionChanged||surfaceChanged)return {changed:true,error:null};
      if(actionDone)return {changed:false,error:actionError};
      await new Promise(resolve=>setTimeout(resolve,50));
    }
  }
"""
new="""  async function waitVoiceActionSettlement(before,actionPromise){
    let actionDone=!(actionPromise&&typeof actionPromise.then==='function'),actionError=null;
    if(!actionDone)Promise.resolve(actionPromise).then(()=>{actionDone=true;},err=>{actionDone=true;actionError=err;console.warn('Ação do Livro iniciada por voz falhou.',err);});
    for(;;){
      const sectionChanged=appState.sectionId!==before.sectionId,current=voiceCurrentSurface(),leftNarrativeSection=!!current&&current.kind!=='section'&&current.key!==before.surfaceKey;
      if(sectionChanged||leftNarrativeSection)return {changed:true,error:null};
      if(actionDone)return {changed:false,error:actionError};
      await new Promise(resolve=>setTimeout(resolve,50));
    }
  }
  async function restartVoiceCycleAfterNavigation(previousSectionId){
    appState.voiceContextKey='';
    appState.voiceLastNarratedStoryKey='';
    appState.voiceLastNarratedPromptKey='';
    if(voiceScheduleTimer){clearTimeout(voiceScheduleTimer);voiceScheduleTimer=null;}
    for(let i=0;i<120&&appState.readingAssistEnabled;i++){
      const surface=voiceCurrentSurface();
      const sectionChanged=appState.sectionId!==previousSectionId;
      const ready=surface&&(surface.kind!=='section'||voiceSectionReady());
      if(sectionChanged&&ready&&!voiceActionPending&&!appState.voiceSpeaking&&!appState.voiceListening&&!voiceMicStarting&&!appState.voiceRecognition&&!voiceSpeechBusy){
        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        await runVoiceCycle(true);
        return true;
      }
      await new Promise(resolve=>setTimeout(resolve,50));
    }
    scheduleVoiceCycle(true,120);
    return false;
  }
"""
if old not in s: raise SystemExit('settlement block not found')
s=s.replace(old,new,1)
old2="""  async function runResolvedVoiceAction(action){if(!action||voiceActionPending)return false;const before=appState.sectionId;cancelVoiceRecognition();voiceActionPending=true;syncVoiceUi();let actionError=null;try{await action.run?.();}catch(err){actionError=err;console.warn('Ação por voz falhou.',err);}finally{voiceActionPending=false;syncVoiceUi();}const advanced=appState.sectionId!==before;if(actionError&&!advanced){if(action.type!=='alternative')await voiceSpeak('A ação ficou indisponível.',{remember:false});else console.warn('Escolha narrativa por voz não concluiu.',actionError);if(appState.readingAssistEnabled){const surface=voiceCurrentSurface();if(surface?.actions?.length){appState.voiceContextKey=surface.key;await startVoiceListening(surface.actions,surface.key,surface.kind==='answer-input'?surface:null);}}return false;}appState.voiceContextKey='';appState.voiceLastNarratedPromptKey='';if(advanced)appState.voiceLastNarratedStoryKey='';scheduleVoiceCycle(true,180);return true;}"""
new2="""  async function runResolvedVoiceAction(action){if(!action||voiceActionPending)return false;const before=appState.sectionId;cancelVoiceRecognition();voiceActionPending=true;syncVoiceUi();let actionError=null;try{await action.run?.();}catch(err){actionError=err;console.warn('Ação por voz falhou.',err);}finally{voiceActionPending=false;syncVoiceUi();}const advanced=appState.sectionId!==before;if(actionError&&!advanced){if(action.type!=='alternative')await voiceSpeak('A ação ficou indisponível.',{remember:false});else console.warn('Escolha narrativa por voz não concluiu.',actionError);if(appState.readingAssistEnabled){const surface=voiceCurrentSurface();if(surface?.actions?.length){appState.voiceContextKey=surface.key;await startVoiceListening(surface.actions,surface.key,surface.kind==='answer-input'?surface:null);}}return false;}if(advanced){await restartVoiceCycleAfterNavigation(before);return true;}appState.voiceContextKey='';appState.voiceLastNarratedPromptKey='';scheduleVoiceCycle(true,180);return true;}"""
if old2 not in s: raise SystemExit('resolved action block not found')
s=s.replace(old2,new2,1)
p.write_text(s)
