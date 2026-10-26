package dcaiv.toolkit;
import zombie.core.Core;
import zombie.ui.UITextEntryInterface;
final class TextEntryState {
    static boolean active() {
        UITextEntryInterface box=Core.currentTextEntryBox;
        return box!=null && box.isDoingTextEntry() && box.isEditable();
    }
}
