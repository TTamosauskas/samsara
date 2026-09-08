from pathlib import Path

p4 = Path('src/js/04-adventure-runtime-render.part.js')
p7 = Path('src/js/07-reading-voice-bootstrap.part.js')
s4 = p4.read_text()
s7 = p7.read_text()

old4 = "b.onclick=()=>{if(action.enabled)return action.execute();};"
new4 = "b.onclick=()=>{if(!action.enabled)return;b._samsaraActionStarted=true;b._samsaraActionError=null;try{const result=action.execute();b._samsaraActionPromise=result;return result;}catch(err){b._samsaraActionError=err;throw err;}};"
assert s4.count(old4) == 1, s4.count(old4)
s4 = s4.replace(old4, new4)

start = s7.index("  async function waitVoiceActionSettlement(")
end = s7.index("  function voiceActionFromAvailableAction", start)
replacement = '''  async function waitVoiceActionSettlement(before,actionPromise){
    let actionDone=!(actionPromise&&typeof actionPromise.then==='function'),actionError=null;
    if(!actionDone)Promise.resolve(actionPromise).then(()=>{actionDone=true;},err=>{actionDone=true;actionError=err;console.warn('Ação do Livro iniciada por voz falhou.',err);});
    for(;;){
      const sectionChanged=appState.sectionId!==before.sectionId,currentKey=voiceSurfaceKeySafe(),surfaceChanged=!!currentKey&&currentKey!==before.surfaceKey;
      if(sectionChanged||surfaceChanged)return {changed:true,error:null};
      if(actionDone)return {changed:false,error:actionError};
      await new Promise(resolve=>setTimeout(resolve,50));
    }
  }
  async function runVoiceNarrativeChoice(index){
    const sectionId=appState.sectionId,section=appState.book?.sections?.[sectionId],choice=section?.choices?.[index];
    if(!choice)throw new Error(`Alternativa ${index+1} não existe na seção atual.`);
    if(bookModeEnabled()&&!appState.editor&&bookPaginationActive()&&appState.bookSubpageCount>1&&appState.bookSubpageIndex<appState.bookSubpageCount-1){renderBookSubpage(appState.bookSubpageCount-1,{commit:true,hint:false});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));}
    const findButton=()=>[...document.querySelectorAll('#choices button[data-choice-index]')].find(btn=>Number(btn.dataset.choiceIndex)===index&&!btn.disabled);
    let button=findButton();
    if(!button){renderChoices();await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));button=findButton();}
    if(!button)throw new Error(`Botão da alternativa ${index+1} não está disponível.`);
    const before={sectionId,surfaceKey:voiceSurfaceKeySafe()};
    button._samsaraActionStarted=false;button._samsaraActionPromise=undefined;button._samsaraActionError=null;
    button.click();
    if(button._samsaraActionError)throw button._samsaraActionError;
    if(!button._samsaraActionStarted)throw new Error(`O clique da alternativa ${index+1} não foi iniciado.`);
    const settled=await waitVoiceActionSettlement(before,button._samsaraActionPromise);
    if(settled.error)throw settled.error;
    return true;
  }
'''
s7 = s7[:start] + replacement + s7[end:]

# Alternative failures should not encourage duplicate execution while state is settling.
old_err = "if(actionError&&!advanced){if(action.type!=='alternative')await voiceSpeak('A ação ficou indisponível.',{remember:false});else toast('Não foi possível concluir essa escolha por voz.');if(appState.readingAssistEnabled){"
new_err = "if(actionError&&!advanced){if(action.type!=='alternative')await voiceSpeak('A ação ficou indisponível.',{remember:false});else console.warn('Escolha narrativa por voz não concluiu.',actionError);if(appState.readingAssistEnabled){"
assert s7.count(old_err) == 1, s7.count(old_err)
s7 = s7.replace(old_err, new_err)

p4.write_text(s4)
p7.write_text(s7)
print('patched')
