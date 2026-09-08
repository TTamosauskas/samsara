from pathlib import Path

p4 = Path('src/js/04-adventure-runtime-render.part.js')
s4 = p4.read_text(encoding='utf-8')
old4 = "b.onclick=()=>{if(action.enabled)action.execute();};"
new4 = "b.onclick=()=>{if(action.enabled)return action.execute();};"
assert s4.count(old4) == 1, f'availableActionButton anchor count: {s4.count(old4)}'
s4 = s4.replace(old4, new4)
p4.write_text(s4, encoding='utf-8')

p7 = Path('src/js/07-reading-voice-bootstrap.part.js')
s7 = p7.read_text(encoding='utf-8')

old_let = "let voiceScheduleTimer=null,voiceObserver=null,voiceSpeechBusy=false,voiceDeferredListen=null,readingMicPermission=null,readingMicPermissionDenied=false,readingMicPermissionPromise=null,voiceMicStarting=false,voiceListenToken=0;"
new_let = "let voiceScheduleTimer=null,voiceObserver=null,voiceSpeechBusy=false,voiceDeferredListen=null,readingMicPermission=null,readingMicPermissionDenied=false,readingMicPermissionPromise=null,voiceMicStarting=false,voiceListenToken=0,voiceActionPending=false;"
assert s7.count(old_let) == 1, 'voice state anchor missing'
s7 = s7.replace(old_let, new_let)

old_run_cycle = "appState.voiceRecognition||voiceSpeechBusy)return;"
new_run_cycle = "appState.voiceRecognition||voiceSpeechBusy||voiceActionPending)return;"
assert s7.count(old_run_cycle) == 1, f'runVoiceCycle guard count: {s7.count(old_run_cycle)}'
s7 = s7.replace(old_run_cycle, new_run_cycle)

start = s7.index('  async function runVoiceNarrativeChoice(index){')
end = s7.index('\n  function voiceActionFromAvailableAction', start)
new_choice = r'''  function voiceSurfaceKeySafe(){try{return voiceCurrentSurface()?.key||'';}catch{return '';}}
  async function waitVoiceActionSettlement(before,actionPromise,timeout=8000){
    let actionDone=!(actionPromise&&typeof actionPromise.then==='function'),actionError=null;
    if(!actionDone)Promise.resolve(actionPromise).then(()=>{actionDone=true;},err=>{actionDone=true;actionError=err;console.warn('Ação do Livro iniciada por voz falhou.',err);});
    const started=performance.now();
    while(performance.now()-started<timeout){
      const sectionChanged=appState.sectionId!==before.sectionId,currentKey=voiceSurfaceKeySafe(),surfaceChanged=!!currentKey&&currentKey!==before.surfaceKey;
      if(sectionChanged||surfaceChanged)return {changed:true,error:null,timeout:false};
      if(actionDone)return {changed:false,error:actionError,timeout:false};
      await new Promise(resolve=>setTimeout(resolve,50));
    }
    return {changed:false,error:actionError,timeout:true};
  }
  async function runVoiceNarrativeChoice(index){
    const sectionId=appState.sectionId,section=appState.book?.sections?.[sectionId],choice=section?.choices?.[index];
    if(!choice)throw new Error(`Alternativa ${index+1} não existe na seção atual.`);
    if(bookModeEnabled()&&!appState.editor&&bookPaginationActive()&&appState.bookSubpageCount>1&&appState.bookSubpageIndex<appState.bookSubpageCount-1){renderBookSubpage(appState.bookSubpageCount-1,{commit:true,hint:false});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));}
    const findButton=()=>[...document.querySelectorAll('#choices button[data-choice-index]')].find(btn=>Number(btn.dataset.choiceIndex)===index&&!btn.disabled);
    let button=findButton();
    if(!button){renderChoices();await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));button=findButton();}
    if(!button)throw new Error(`Botão da alternativa ${index+1} não está disponível.`);
    const handler=button.onclick;
    if(typeof handler!=='function')throw new Error(`A alternativa ${index+1} não possui ação executável.`);
    const before={sectionId,surfaceKey:voiceSurfaceKeySafe()};
    let actionPromise;
    try{actionPromise=handler.call(button,new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));}catch(err){throw err;}
    const settled=await waitVoiceActionSettlement(before,actionPromise);
    if(settled.error)throw settled.error;
    if(settled.timeout)throw new Error(`A alternativa ${index+1} não concluiu nem abriu uma nova etapa.`);
    return true;
  }'''
s7 = s7[:start] + new_choice + s7[end:]

old_resolved_start = s7.index('  async function runResolvedVoiceAction(action){')
old_resolved_end = s7.index('\n  async function confirmVoiceAction', old_resolved_start)
new_resolved = r'''  async function runResolvedVoiceAction(action){if(!action||voiceActionPending)return false;const before=appState.sectionId;cancelVoiceRecognition();voiceActionPending=true;syncVoiceUi();let actionError=null;try{await action.run?.();}catch(err){actionError=err;console.warn('Ação por voz falhou.',err);}finally{voiceActionPending=false;syncVoiceUi();}const advanced=appState.sectionId!==before;if(actionError&&!advanced){if(action.type!=='alternative')await voiceSpeak('A ação ficou indisponível.',{remember:false});else toast('Não foi possível concluir essa escolha por voz.');if(appState.readingAssistEnabled){const surface=voiceCurrentSurface();if(surface?.actions?.length){appState.voiceContextKey=surface.key;await startVoiceListening(surface.actions,surface.key,surface.kind==='answer-input'?surface:null);}}return false;}appState.voiceContextKey='';appState.voiceLastNarratedPromptKey='';if(advanced)appState.voiceLastNarratedStoryKey='';scheduleVoiceCycle(true,180);return true;}'''
s7 = s7[:old_resolved_start] + new_resolved + s7[old_resolved_end:]

p7.write_text(s7, encoding='utf-8')
