def show_toast(driver, message, duration=2000):
    js = f"""
    (function(){{
        var existing = document.getElementById('custom-toast');
        if (existing) existing.remove();

        var toast = document.createElement('div');
        toast.id = 'custom-toast';
        toast.innerText = `{message}`;
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.backgroundColor = 'rgba(0,0,0,0.7)';
        toast.style.color = 'white';
        toast.style.padding = '10px 20px';
        toast.style.borderRadius = '5px';
        toast.style.zIndex = 9999;
        toast.style.fontSize = '16px';
        toast.style.fontFamily = 'Arial, sans-serif';
        toast.style.transition = 'opacity 0.5s';
        toast.style.opacity = '1';
        document.body.appendChild(toast);

        setTimeout(function(){{
            toast.style.opacity = '0';
            setTimeout(function(){{ toast.remove(); }}, 500);
        }}, {duration});
    }})();
    """
    driver.execute_script(js)
