(function () {
    function getSelectedBox() {
        return (
            document.getElementById("id_condicoes_saude_to") ||
            document.getElementById("id_condicoes_saude") ||
            document.querySelector("#id_condicoes_saude_to") ||
            document.querySelector("#id_condicoes_saude") ||
            document.querySelector(".selector-chosen select") ||
            document.querySelector(".field-condicoes_saude select")
        );
    }

    function initCondicoesDescricoes() {
        const selectedBox = getSelectedBox();
        const hiddenInput = document.getElementById("id_descricoes_condicoes_json");

        console.log("selectedBox:", selectedBox);
        console.log("hiddenInput:", hiddenInput);

        if (!selectedBox || !hiddenInput) return false;
        if (document.getElementById("condicoes-descricoes-row")) return true;

        let descricoes = {};
        try {
            descricoes = JSON.parse(hiddenInput.value || "{}");
        } catch (e) {
            descricoes = {};
        }
        const condicoesFieldRow =
            selectedBox.closest(".form-row") ||
            selectedBox.closest(".aligned") ||
            document.querySelector(".form-row.field-condicoes_saude") ||
            document.querySelector(".field-condicoes_saude") ||
            selectedBox.closest(".fieldBox");

        const referenciaRow =
            document.getElementById("id_descricao")?.closest(".form-row") ||
            document.getElementById("id_descricao")?.closest(".aligned") ||
            document.querySelector(".form-row.field-descricao") ||
            document.querySelector(".field-descricao") ||
            document.getElementById("id_descricao")?.closest(".fieldBox");

        const referenciaInput = document.getElementById("id_descricao");

        let larguraLabel = 260;
        let larguraCampo = 980;
        let gap = 28;

        if (referenciaRow && referenciaInput) {
            const rowRect = referenciaRow.getBoundingClientRect();
            const inputRect = referenciaInput.getBoundingClientRect();
            larguraLabel = Math.max(180, Math.round(inputRect.left - rowRect.left - gap));
            larguraCampo = Math.round(inputRect.width);
        }

        const row = document.createElement("div");
        row.id = "condicoes-descricoes-row";
        row.style.display = "grid";
        row.style.gridTemplateColumns = `${larguraLabel}px minmax(0, ${larguraCampo}px)`;
        row.style.columnGap = `${gap}px`;
        row.style.alignItems = "start";
        row.style.margin = "18px 0";
        row.style.width = "100%";
        row.style.boxSizing = "border-box";

        const left = document.createElement("div");
        left.style.paddingTop = "8px";

        const leftLabel = document.createElement("label");
        leftLabel.textContent = "Descrição por condição de saúde";
        leftLabel.style.fontWeight = "600";
        leftLabel.style.fontSize = "13px";
        leftLabel.style.color = "#111";
        left.appendChild(leftLabel);

        const right = document.createElement("div");
        right.style.width = "100%";
        right.style.maxWidth = `${larguraCampo}px`;

        const subtitle = document.createElement("div");
        subtitle.textContent = "Preencha uma descrição específica para cada condição selecionada.";
        subtitle.style.fontSize = "12px";
        subtitle.style.color = "#6b7280";
        subtitle.style.marginBottom = "12px";

        const container = document.createElement("div");
        container.id = "condicoes-descricoes-container";
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.gap = "14px";

        right.appendChild(subtitle);
        right.appendChild(container);

        row.appendChild(left);
        row.appendChild(right);

        if (referenciaRow) {
        referenciaRow.insertAdjacentElement("beforebegin", row);
    } else if (condicoesFieldRow) {
        condicoesFieldRow.insertAdjacentElement("afterend", row);
    }

        function getSelectedOptions() {
            if (selectedBox.tagName === "SELECT") {
                return Array.from(selectedBox.options);
            }
            return [];
        }

        function getSelectedIds() {
            return getSelectedOptions().map(opt => String(opt.value));
        }

        function syncDescricoes() {
            const selectedIds = getSelectedIds();

            Object.keys(descricoes).forEach(key => {
                if (!selectedIds.includes(key)) {
                    delete descricoes[key];
                }
            });

            hiddenInput.value = JSON.stringify(descricoes);
        }

        function createCard(condicaoId, condicaoNome) {
            const card = document.createElement("div");
            card.style.background = "#fff";
            card.style.border = "1px solid #d7dce1";
            card.style.borderRadius = "8px";
            card.style.padding = "12px 14px";

            const title = document.createElement("div");
            title.textContent = condicaoNome;
            title.style.fontSize = "13px";
            title.style.fontWeight = "600";
            title.style.marginBottom = "4px";

            const helper = document.createElement("div");
            helper.textContent = "Descrição específica para esta condição de saúde";
            helper.style.fontSize = "12px";
            helper.style.color = "#6b7280";
            helper.style.marginBottom = "8px";

            const textarea = document.createElement("textarea");
            textarea.rows = 4;
            textarea.value = descricoes[condicaoId] || "";
            textarea.style.width = "100%";
            textarea.style.minHeight = "110px";
            textarea.style.boxSizing = "border-box";
            textarea.style.padding = "10px 12px";
            textarea.style.border = "1px solid #cbd5e1";
            textarea.style.borderRadius = "6px";
            textarea.style.resize = "vertical";

            textarea.addEventListener("input", function () {
                descricoes[condicaoId] = textarea.value;
                hiddenInput.value = JSON.stringify(descricoes);
            });

            card.appendChild(title);
            card.appendChild(helper);
            card.appendChild(textarea);

            return card;
        }

        function renderCampos() {
            container.innerHTML = "";

            const selectedOptions = getSelectedOptions();

            if (selectedOptions.length === 0) {
                const empty = document.createElement("div");
                empty.textContent = "Selecione uma ou mais condições de saúde para liberar os campos de descrição.";
                empty.style.padding = "14px";
                empty.style.background = "#fff";
                empty.style.border = "1px dashed #cbd5e1";
                empty.style.borderRadius = "8px";
                container.appendChild(empty);
                syncDescricoes();
                return;
            }

            selectedOptions.forEach(option => {
                const condicaoId = String(option.value);
                const condicaoNome = option.text;
                container.appendChild(createCard(condicaoId, condicaoNome));
            });

            syncDescricoes();
        }

        const observer = new MutationObserver(renderCampos);
        observer.observe(selectedBox, { childList: true, subtree: true });

        selectedBox.addEventListener("change", renderCampos);

        const form = selectedBox.closest("form");
        if (form) {
            form.addEventListener("submit", function () {
                syncDescricoes();
            });
        }

        renderCampos();
        return true;
    }

    function startWhenReady() {
        let tries = 0;
        const maxTries = 60;

        const interval = setInterval(function () {
            tries += 1;
            const ok = initCondicoesDescricoes();
            if (ok || tries >= maxTries) clearInterval(interval);
        }, 300);
    }

    document.addEventListener("DOMContentLoaded", startWhenReady);
})();