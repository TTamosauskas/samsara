from pathlib import Path
import re

path = Path('src/js/07-reading-voice-bootstrap.part.js')
s = path.read_text()

def sub_once(pattern, repl, text, flags=0, label='replacement'):
    out, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 replacement, got {n}')
    return out

# 1) Ordinary pointer interaction must not interrupt narration.
old = "const actionish=!!e.target.closest?.('#sectionActions button,#npcBox button,#combatBox button,#choices button,#inventoryDialog button,dialog button');cancelVoiceRecognition();interruptVoiceSpeech();appState.voiceContextKey='';if(actionish)setTimeout(()=>scheduleVoiceCycle(true,320),150);"
new = "const actionish=!!e.target.closest?.('#sectionActions button,#npcBox button,#combatBox button,#choices button,#inventoryDialog button,dialog button');if(!actionish)return;voiceDeferredListen=null;cancelVoiceRecognition();appState.voiceContextKey='';setTimeout(()=>scheduleVoiceCycle(true,320),150);"
if s.count(old) != 1:
    raise SystemExit(f'pointerdown patch: expected 1 target, got {s.count(old)}')
s = s.replace(old, new)

# If a real action changes context while the current utterance finishes,
# immediately start the narration cycle for the new surface afterwards.
old = "if(ok&&deferred&&appState.readingAssistEnabled)setTimeout(()=>startVoiceListening(deferred.actions,deferred.contextKey,deferred.answerSurface),160);resolve(ok);"
new = "if(ok&&deferred&&appState.readingAssistEnabled)setTimeout(()=>startVoiceListening(deferred.actions,deferred.contextKey,deferred.answerSurface),160);else if(ok&&appState.readingAssistEnabled&&!appState.voiceContextKey)setTimeout(()=>scheduleVoiceCycle(true,80),80);resolve(ok);"
if s.count(old) != 1:
    raise SystemExit(f'voice finish patch: expected 1 target, got {s.count(old)}')
s = s.replace(old, new)

# 2 + 4) Narrative actions come from the domain model, not only buttons that
# happen to be visible on the current paginated leaf. Their async execute()
# functions are returned directly so runResolvedVoiceAction can await them.
replacement = """  function voiceActionFromAvailableAction(spec,type='action'){if(!spec||spec.enabled===false)return null;const label=voiceCleanLabel(spec.label||'');if(!label)return null;return {type,label,sourceId:spec.id||'',aliases:[label,...voiceCommonAliases(label)],run:()=>spec.execute?.()};}
  function collectNarrativeVoiceActions(){const actions=collectVoiceActionsFromSelectors(['#sectionActions button','#endingPanel button']);const s=appState.book?.sections?.[appState.sectionId],seen=new Set(actions.map(a=>`${a.type}|${voiceNormalize(a.label)}|${a.button?.id||''}`));for(const spec of getAvailableActions('choice',{section:s})){const action=voiceActionFromAvailableAction(spec,spec.kind==='narrative'?'alternative':'action');if(!action)continue;const key=`${action.type}|${voiceNormalize(action.label)}|${action.sourceId}`;if(seen.has(key))continue;seen.add(key);actions.push(action);}actions.forEach((a,i)=>addVoiceOrdinalAliases(a,i+1));return actions;}"""
s = sub_once(r'^  function collectNarrativeVoiceActions\(\)\{.*\}$', replacement, s, re.M, 'narrative actions patch')

# 3) Read one concise invitation before the alternatives and remove the old
# trailing instruction. runVoiceCycle already starts the microphone when the
# prompt utterance finishes.
replacement = "  function voicePromptForActions(actions=[],lead='O que você faz?'){if(!actions.length)return '';return `${lead} ${actions.map((a,i)=>`${a.ordinal||i+1}, ${voiceCleanLabel(a.label)}.`).join(' ')}`;}"
s = sub_once(r'^  function voicePromptForActions\(actions=\[\],lead=.*$', replacement, s, re.M, 'voice prompt patch')
s = s.replace("voicePromptForActions(actions,'Opções:')", "voicePromptForActions(actions)")

path.write_text(s)
