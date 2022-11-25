if (document.querySelector("#user-phone")) {
    const tel = document.querySelector("#user-phone");

    const telPattern = {
        mask: '{(}00{)} 00000{-}0000'
    }

    const telMasked = IMask(tel, telPattern);
}