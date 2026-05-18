// inline edit helpers
function _inlineEdit(showBtnId, formId, cancelBtnId) {
    document.getElementById(showBtnId)?.addEventListener('click', () => {
        document.getElementById(formId).style.display = 'block';
    });
    document.getElementById(cancelBtnId)?.addEventListener('click', () => {
        document.getElementById(formId).style.display = 'none';
    });
}
_inlineEdit('editNameBtn',  'editNameForm',  'cancelNameBtn');
_inlineEdit('editEmailBtn', 'editEmailForm', 'cancelEmailBtn');
_inlineEdit('editPhoneBtn', 'editPhoneForm', 'cancelPhoneBtn');
