export const showMessage = (msg, options = {}) => {
    const notification = (options.notification !== undefined) ? options.notification : true;

    if (notification && Notification.permission === "granted") {
        new Notification("ACCB Price Miner", { body: msg });
    }

    Materialize.toast(msg, 8000, "rounded");
};
