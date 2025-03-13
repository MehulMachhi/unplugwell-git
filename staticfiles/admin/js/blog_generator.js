document.addEventListener('DOMContentLoaded', function() {
    const titleField = document.getElementById('id_title');
    if (!titleField) return;

    // Create and add the generate button

    const response = await fetch('/generate-content/', {  // Updated URL
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
    },
    body: JSON.stringify({ topic })
});
    const generateButton = document.createElement('button');
    generateButton.type = 'button';
    generateButton.className = 'button';
    generateButton.textContent = '🤖 Generate Content';
    generateButton.style.marginLeft = '10px';
    titleField.parentNode.insertBefore(generateButton, titleField.nextSibling);

    generateButton.addEventListener('click', async function(e) {
        e.preventDefault();
        const topic = titleField.value.trim();

        if (!topic) {
            alert('Please enter a topic in the title field first');
            return;
        }

        generateButton.disabled = true;
        generateButton.textContent = '🤖 Generating...';

        try {
            const response = await fetch('/admin/Blog/post/generate-content/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: JSON.stringify({ topic })
            });

            const data = await response.json();
            if (data.success) {
                // Find and update CKEditor instance
                for (let instance in CKEDITOR.instances) {
                    if (instance === 'id_content') {
                        CKEDITOR.instances[instance].setData(data.content);
                    }
                }

                // Update other fields
                document.getElementById('id_excerpt').value = data.excerpt;
                document.getElementById('id_meta_title').value = data.meta_title;
                document.getElementById('id_meta_description').value = data.meta_description;
                document.getElementById('id_focus_keywords').value = data.focus_keywords;
            } else {
                alert(data.error || 'Error generating content');
            }
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            generateButton.disabled = false;
            generateButton.textContent = '🤖 Generate Content';
        }
    });
});