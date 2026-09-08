from pathlib import Path
import re

p=Path('src/js/07-reading-voice-bootstrap.part.js')
s=p.read_text()

old="function voiceActionFromAvailableAction(spec,type='action'){if(!spec||spec.enabled===false)return null;const label=voiceCleanLabel(spec.label||'');if(!label)return null;return {type,label,sourceId:spec.id||'',aliases:[label,...voiceCommonAliases(label)],run:()=>spec.execute?.()};}"
new="""async function runVoiceNarrativeChoice(index){const section=appState.book?.sections?.[appState.sectionId],choice=section?.choices?.[index];if(!choice)throw new Error(`Alternativa ${index+1} não existe na seção atual.`);if(bookModeEnabled()&&!appState.editor&&bookPaginationActive()&&appState.bookSubpageCount>1&&appState.bookSubpageIndex<appState.bookSubpageCount-1){renderBookSubpage(appState.bookSubpageCount-1,{commit:true,hint:false});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));}return choose(choice,index);}
  function voiceActionFromAvailableAction(spec,type='action'){if(!spec||spec.enabled===false)return null;const label=voiceCleanLabel(spec.label||'');if(!label)return null;const index=Number(spec.dataset?.choiceIndex),narrative=type==='alternative'&&Number.isInteger(index)&&index>=0;return {type,label,sourceId:spec.id||'',aliases:[label,...voiceCommonAliases(label)],run:narrative?()=>runVoiceNarrativeChoice(index):()=>spec.execute?.()};}"""
if s.count(old)!=1: raise SystemExit(f'voiceActionFromAvailableAction target count={s.count(old)}')
s=s.replace(old,new,1)

pat=r"^  async function runResolvedVoiceAction\(action\)\{.*\}$"
rep="""  async function runResolvedVoiceAction(action){if(!action)return false;const before=appState.sectionId;cancelVoiceRecognition();let actionError=null;try{await action.run?.();}catch(err){actionError=err;console.warn('Ação por voz falhou.',err);}const advanced=appState.sectionId!==before;if(actionError&&!advanced){await voiceSpeak('A ação ficou indisponível.',{remember:false});if(appState.readingAssistEnabled){const surface=voiceCurrentSurface();if(surface?.actions?.length){appState.voiceContextKey=surface.key;await startVoiceListening(surface.actions,surface.key,surface.kind==='answer-input'?surface:null);}}return false;}appState.voiceContextKey='';appState.voiceLastNarratedPromptKey='';if(advanced)appState.voiceLastNarratedStoryKey='';scheduleVoiceCycle(true,420);return true;}"""
s,n=re.subn(pat,rep,s,count=1,flags=re.M)
if n!=1: raise SystemExit(f'runResolvedVoiceAction target count={n}')

p.write_text(s)
